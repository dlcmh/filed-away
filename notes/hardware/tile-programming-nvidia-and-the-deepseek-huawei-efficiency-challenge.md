# Tile programming, Nvidia, and the DeepSeek–Huawei efficiency challenge

> A thematic reorganization of a long conversation on accelerator abstractions, the economics of inference, export control, and AI diffusion in China.
>
> Source: [shared conversation](https://chat.deepseek.com/share/zjq8dkuenu6nssm0qs) on chat.deepseek.com. 34 questions, 34 answers. The source link expires when the conversation is deleted from DeepSeek. This note reorganizes the conversation by subject rather than by turn; claims, figures, and attributions are those of the conversation and its cited sources, dated November 2026, and passages that the conversation itself marked as rumour are identified as such.

The conversation begins with a question about a tutorial on accelerator programming and ends, thirty-four turns later, on the verification bottleneck in mathematics. Between those points it develops a single argument through several unrelated bodies of evidence: that the competitive axis in AI hardware has moved from peak arithmetic throughput to cost per token, that the software layer is where that shift is being decided, and that both the American control regime and Nvidia's own marketing are organized around the previous axis. The subjects below are ordered from the programming model outward: execution abstractions, then the hardware that embodies them, then the economics those products serve, then the political and corporate structures around them, and finally the diffusion and hype patterns that make the shift difficult to see.

## Two programming models: schedules and tiles

The distinction that opens the conversation is between two ways of describing work to an accelerator. In the SIMT model that CUDA exposes, the programmer writes code for individual threads, manages indexing, allocates shared memory, and inserts synchronization barriers. The hardware warp scheduler performs the latency hiding: it switches among resident warps so that memory stalls on one warp are covered by instruction issue from another. Throughput is therefore a function of occupancy and of the programmer's ability to keep enough independent work resident.

In the tile model, the unit of composition is a two-dimensional block of data rather than a thread. The programmer describes dataflow — which tiles are loaded, where they are staged, which operation consumes them — and the compiler generates the low-level load, store, and synchronization instructions. The tutorial the conversation examines names this the "separation of dataflow and schedule", and treats the compiler's schedule, not the instruction set, as the dominant performance factor.

| Model | Core abstraction | What the programmer manages | What is hidden |
| --- | --- | --- | --- |
| SIMT GPU (CUDA) | Threads in warps, caches, barriers | Thread indexing, shared memory, synchronization | Scheduling, latency, cache behaviour |
| Tile NPU | 2D tiles, explicit on-chip buffers, DMA engines | Data movement, tile shape, buffer placement | Operator eligibility, generated schedule |

The practical consequence is a change in what performance analysis consists of. On a GPU, the analysis is about occupancy, bank conflicts, and divergence. On a tile machine it is about whether data arrives at the compute units at the required rate. Neither model is strictly higher-level than the other; they place the scheduling responsibility in different places.

## Whether a machine can be programmed in tiles

The decision to use a tile compiler such as TileLang is, first, a hardware compatibility question. TileLang does not create hardware features; it emits code for backends selected by a target specification. The targets documented at the time of the conversation include `cuda` (Nvidia, CUDA toolkit 10.0 or later), `hip` (AMD, through ROCm), `metal` (Apple silicon GPUs), `ascend` (Huawei, requiring CANN 8.3.RC1 or later and `torch_npu` 2.6.0 or later), and `cpu`.

A target is necessary but not sufficient. The hardware must also admit the abstraction, or the compiler must contain a lowering path that maps tiles onto that hardware's actual execution model. The taxonomy used in the conversation divides accelerators into three classes:

- **Tile NPUs** (Ascend, the Apple Neural Engine, TPU) expose tiles, on-chip buffers, and DMA directly. The tile abstraction is the native one.
- **SIMT GPUs** (Nvidia, AMD, Apple GPUs) are programmer-visible thread machines. A tile compiler can target them, but it must bridge the abstraction gap, and tuning may still require reasoning about the generated thread schedule.
- **Dataflow machines** (for example Tenstorrent) expose explicit streams and queues; whether a tile compiler has a suitable backend must be verified rather than assumed.

The resulting decision procedure is short: confirm a backend exists, identify which of the three classes the hardware belongs to, and treat an unsupported or exotic architecture as a high-risk starting point rather than a portability problem to be solved later.

## The Apple Neural Engine: tile execution behind a closed interface

Apple's Neural Engine is the clearest example of tile hardware that a tile compiler cannot reach. The engine is tile-oriented internally — reverse-engineering work describes a `TileDMA` that copies input tiles from DRAM into on-chip memory, rows of MAC units that process tiles, and a second DMA that writes results back — but there is no public programming interface. The only supported access path is Core ML, which uses the private `AppleNeuralEngine.framework` internally; applications that link against that framework are rejected during App Store review.

The contrast with Apple's other accelerators is exact: the GPU has Metal, the CPU has Accelerate and BNNS, and the neural engine has no public interface at all. The consequence for TileLang on Apple silicon is that its Apple target is the Metal backend for the GPU, not the neural engine. A kernel written in tiles on an M-series machine is executing on a SIMT GPU, not on the tile accelerator that the abstraction would otherwise fit. The engine remains reachable in practice only through Core ML as an intermediary, or through private interfaces such as `_ANEClient` and `_ANEInMemoryModelDescriptor`, which are a research path rather than a production foundation.

## Why inference maps onto tile hardware

The fit between tile hardware and inference is structural rather than analogical, and the conversation sets out five properties that produce it.

**Static, compilable dataflow.** Inference is a forward pass through a fixed graph, with no backward pass, gradient accumulation, or optimizer state. Tile sizes, buffer allocation, and DMA pipelining can therefore be fixed ahead of execution, which is precisely what the separation of dataflow and schedule assumes. Training contains dynamic elements — loss-dependent gradients, optimizer updates, loss scaling — that resist fully static scheduling.

**Dense linear algebra dominates.** Inference consists largely of GEMMs, convolutions, and element-wise operations, all of which decompose into 2D tiles that can be staged into SRAM and fed to MAC arrays.

**Precision tolerance.** Inference tolerates INT8, FP8, and in some cases INT4 with limited accuracy loss, and tile-based MAC arrays are commonly designed for blocked low-precision formats. Training requires higher precision and is more sensitive to numerical degradation.

**Memory-bound streaming rather than latency hiding.** Weights are fixed, so the central problem is moving weights and activations through a limited hierarchy: DRAM, L2, on-chip SRAM, MACs. The appropriate mental model is orchestration of data movement, which the ANE's `TileDMA` expresses directly.

**Deterministic latency.** Edge inference has hard timing targets, and tile NPUs are built for pipelineable execution with predictable timing, unlike GPUs whose latency depends on occupancy dynamics.

The fit is not unconditional. Prefill is compute-bound and GEMM-like, which suits the model well; decode at batch size one is memory-bandwidth-bound, so the bottleneck moves to weight streaming. Variable sequence lengths, mixture-of-experts routing, and conditional computation complicate static tiling. Structured sparsity tiles cleanly; unstructured sparsity does not.

## On-chip memory: presence and management

A common misreading is that Nvidia's AI GPUs lack on-chip memory. They do not. A Hopper or Blackwell part carries a full hierarchy: registers private to each thread (a 256 KB register file per SM on recent architectures), a combined shared-memory and L1 SRAM block inside each SM (256 KB per SM on H100, 128 KB per SM by default on B200), a shared L2 (50 MB on H100, 126 MB on B200), and on Blackwell a dedicated tensor memory (TMEM) with explicit software-managed transfers for tensor-core operands.

The distinction that matters is one of management rather than existence:

- **On an Nvidia GPU**, shared memory is a software-managed scratchpad that the programmer can allocate and fill explicitly, while L1 and L2 behave as hardware-managed caches and the warp scheduler controls latency hiding. The programmer has explicit control over one region of the hierarchy and no direct control over the rest.
- **On a tile NPU**, the equivalent buffer (the Unified Buffer on Ascend) is typically managed by the compiler rather than the programmer, data movement is performed by dedicated DMA engines, and the hierarchy is segmented rather than partly unified into a cache.

This is also why CUDA tiling works at all: a tiled matrix multiply in CUDA is an explicit load of tiles into shared memory, using the software-managed portion of the hierarchy for reuse. The tile abstraction is already the standard technique on GPUs. The complication is the hybrid character of the hierarchy: explicit staging coexists with implicit caching, and a compiler mapping tiles onto a GPU must bridge the two.

## The managed-runtime analogy

The conversation tests an analogy between CUDA's hybrid memory model and a language with automatic memory reclamation, and finds it productive in one respect and misleading in another.

The productive part is the structure of control: the programmer explicitly manages part of the resource while a runtime manages the rest, which yields productivity at the cost of determinism. The failure modes also correspond. Cache thrashing is the memory analogue of a collection pause: timing-dependent, difficult to attribute, and often triggered by access patterns the programmer did not consider. The corresponding skill is the same in both cases — cooperate with the implicit layer rather than attempt to outmanoeuvre it.

The analogy breaks in three places. Automatic reclamation manages object lifetime, while caches manage locality; these are orthogonal concerns that happen to share a control structure, and a cache does not reclaim, it replicates speculatively. The GPU exposes more tuning controls than a managed runtime: the L1/shared-memory split is configurable, cache hints and explicit prefetches exist, and data can be pinned in L2, so the implicit layer is partially steerable. Finally, a collection pause is non-deterministic in timing, whereas a cache miss is deterministic in principle and merely opaque in practice.

| Layer | CUDA | Managed language | Tile NPU |
| --- | --- | --- | --- |
| Explicit scratchpad | Shared memory | Manual allocation | Compiler-managed buffer |
| Implicit management | L1/L2 caches, warp scheduler | Collector, JIT layout | Compiler schedule and DMA |
| Scheduling | Hardware warp scheduler | Runtime thread scheduler | Static compile-time plan |
| Performance cliff | Cache thrash, bank conflicts | Collection pause | Poor tile size, DMA stall |

Pushed this far, the analogy inverts its own conclusion: the tile NPU is more like a managed runtime than the GPU is, because the compiler manages both the buffers and the schedule. The GPU's hybrid model — manual allocation alongside automatic caching — is the unusual case. The warp scheduler is better compared to a runtime scheduler for green threads, and on a tile machine that scheduler is replaced by a compile-time plan, which is why the tutorial treats the schedule as the performance factor.

## Integration versus separation: Nvidia's tensor cores and the client NPU

Apple and Nvidia resolve the accelerator question differently. Apple separates engines: a GPU, a neural engine, and a CPU, each optimized for a workload class and a power envelope. Nvidia integrates: AI acceleration is implemented as tensor cores inside the GPU die, so that the programmer, the compiler, and the hardware all address one programmable engine with specialized functional units.

The integration thesis holds for the data-center and graphics lines but not for the client platform. In 2026 Nvidia introduced RTX Spark, a single package for Windows laptops and desktops containing an Arm CPU, a Blackwell RTX GPU, and a dedicated NPU. The separation exists in a client product and does not reverse the data-center architecture: Nvidia's materials present the GPU's tensor cores as the primary AI engine, with the NPU as a lower-power block for background workloads that can run while the GPU is idle. The pattern is integration for throughput at scale and separation for power-constrained edge devices.

## One die, two memory systems: Ascend 950PR and 950DT

Huawei's Ascend 950 splits its product line along a different axis. Both variants use the same Ascend 950 die and the third-generation DaVinci core, and both deliver 804 TFLOPS in FP8. The difference is the memory system, and it corresponds to two different bottlenecks.

| | Ascend 950PR | Ascend 950DT |
| --- | --- | --- |
| Primary target | Inference prefill, recommendation systems | Inference decode, model training |
| Memory | HiBL 1.0, a non-HBM cost-optimized path | HiZQ 2.0, proprietary high-bandwidth memory |
| Capacity | 112 GB or 128 GB, typically 128 GB | 96 GB or 144 GB, typically 144 GB |
| Bandwidth | 1.4 TB/s or 1.6 TB/s, typically 1.6 TB/s | up to 4 TB/s |
| Rationale | cost-efficient for compute-bound phases | bandwidth-first for memory-bound phases |

The segmentation is finer than a training-versus-inference divide. Prefill is a dense matrix multiplication in which the 804 TFLOPS can be saturated, so pairing it with cheaper memory lowers total cost of ownership without limiting the compute-bound phase. Decode and training are limited by the rate at which weights and activations can be moved, so the higher-bandwidth memory is not optional. Huawei's published roadmap indicates that the 960 and 970 generations continue the same dual-track pattern.

## The top of the Nvidia stack: Blackwell and Vera Rubin

The most expensive Nvidia parts are not general-purpose graphics cards but the capital equipment of model training and serving. The conversation separates three missions.

**Frontier training.** Trillion-parameter models trained from scratch require maximum throughput, memory capacity, and interconnect bandwidth. The B200 serves as the production workhorse; the B300 (Blackwell Ultra) offers a training advantage through 288 GB of memory and faster networking; the GB200 and GB300 NVL72 rack systems are positioned for trillion-parameter and mixture-of-experts training.

**High-volume inference.** Much of the installed base serves rather than trains models, which is a memory-bandwidth-bound problem, so parts with the most HBM and bandwidth command a premium. The B300's 288 GB is justified by long-context inference at high concurrency and by single-GPU serving of very large models.

**Agentic reasoning.** Vera Rubin is positioned for multi-step reasoning, long-context workflows, and tool use, with a dedicated inference accelerator (Groq 3 LPX) paired with the GPUs to address low-latency, large-context demands.

Vera Rubin itself is a multi-rack architecture rather than a single system. Its components are:

- **Vera CPU** — an Arm host processor with 88 custom "Olympus" cores per socket, SMT2 for 176 threads per socket, and LPDDR5X memory.
- **Rubin GPU** — 288 GB of HBM4 at up to 22 TB/s and 50 PFLOPs of NVFP4 performance per package.
- **NVLink 6 switch** — 1.8 TB/s of coherent bandwidth, described by Nvidia as seven times PCIe Gen 6.

A Vera Rubin NVL72 rack contains 72 Rubin GPUs, 36 Vera CPUs, 18 compute trays (two CPUs and four GPUs each), 9 NVLink 6 switch trays with four switch ASICs each, 18 BlueField-4 DPUs for north-south traffic, and 144 ConnectX-9 NIC ASICs for east-west scale-out. Adjacent rack types target specific phases: the Rubin CPX rack pairs 144 CPX GPUs with 128 GB of GDDR7 each with 144 standard Rubin GPUs and 36 Vera CPUs for the prefill and context phase; a liquid-cooled Vera CPU rack holds 256 CPUs for reinforcement learning, tool calls, and orchestration.

Prices follow the positioning: a single B200 is quoted at \$30,000 to \$50,000, and a complete GB200 NVL72 rack exceeds \$3 million.

## Naming: the DPU question

The conversation pauses on terminology because the terminology is doing commercial work. "Data Processing Unit" describes any processor, and the component it names — the BlueField-4 in a Vera Rubin rack — performs networking, security, storage virtualization, telemetry, and control-plane offload. Nvidia popularized the term around 2020 after acquiring Mellanox, largely to create a product category from what the industry had called a smartNIC and to position it as a third pillar alongside CPU and GPU. Intel's competing term, Infrastructure Processing Unit, names the problem being solved rather than the generic activity being performed.

Functionally, the BlueField-4 is a server within a server: Arm cores, memory, PCIe switching, and accelerators for cryptography, compression, and networking, sitting on the fabric between the GPU domain and the outside world. It is what allows the GPU domain to remain isolated and secure while participating in a coherent fabric, which is architecturally significant work described by an uninformative acronym.

## Co-design: DeepInfer, FlashMLA, and the service economics

The DeepSeek–Huawei collaboration is the mechanism behind the cost and latency figures discussed later, and the conversation describes it as full-stack co-design rather than chip adoption.

- **DeepInfer**, DeepSeek's production inference engine, was released under Apache 2.0 with a hardware abstraction layer: one codebase runs on Nvidia GPUs and Huawei Ascend NPUs, selected by the `DEEPINFER_ACCELERATOR` environment variable. The Ascend path is the same engine, not a reduced fork.
- **FlashMLA** kernels for the Ascend 950 reach up to 410 TFLOPS during prefill (95% of hardware peak) and 360 TFLOPS during decode (83% of peak), leaving little compute unused relative to a less-optimized stack.
- The collaboration extends to tooling: `DeepGEMM`, `DeepEP` for communication, and TileLang compiler support, all intended to make Ascend a first-class development target.

The service consequences are visible in Malaysia, where the chat application is free, ad-free, available without a VPN, and supports Malay. Pricing for API access is far below Western comparators: V4.1-Flash output at roughly \$0.60 per million tokens against \$30.00 for a comparable GPT model, V4-Pro output at roughly \$3.96 per million against Claude Sonnet 5, and an 80,000-word processing task at about RM 14 against roughly RM 80 with OpenAI. Single-user generation runs at 175 to 184 tokens per second. The argument is that these figures follow from the compiler and kernel work rather than from subsidized pricing.

## Capacity and consumption: 155 trillion against 8 trillion

Two figures circulate for DeepSeek's token volume, and the conversation distinguishes them carefully because they measure different quantities.

| Figure | What it measures | Scope |
| --- | --- | --- |
| 155 trillion tokens/day | Throughput capacity of one optimized cluster running V4.1-Flash on DeepInfer | A single cluster |
| approximately 8 trillion tokens/day | Actual aggregate volume attributed to DeepSeek | Company-wide service |

The 155 trillion figure is a capability claim from deployment notes: what a saturated cluster can serve. It corresponds to roughly 1.8 million tokens per second, about 6.5 billion tokens per hour, and — at roughly 2,000 tokens per conversation — enough capacity for 77.5 billion conversations per day. The ~8 trillion figure is a disclosed or observed consumption number, which may cover API traffic only, may be rounded, and reflects a mixed model fleet in which Pro-tier and long-context requests consume far more compute per token than Flash-tier ones. A cluster rated for a given throughput does not necessarily serve it; utilization, demand, and model mix intervene.

The ceiling is reached through compounding efficiencies rather than raw chip throughput:

- **Batching at scale** keeps MAC arrays saturated until memory or latency limits bind.
- **Prefill/decode disaggregation** runs the compute-bound prefill phase on standard 8-GPU nodes and the memory-bound decode phase on 64-to-128-GPU supernodes.
- **KV-cache retention** holds context for up to seven days, backed by roughly 100 PiB of SSD storage, which removes repeated prefill work for long-running and agentic sessions.
- **Kernel-level optimization** at 95% and 83% of peak leaves little headroom unused.
- **Cheap power** — about 4.7 cents per kWh in Inner Mongolia — lowers the marginal cost of running the cluster at capacity.

At off-peak electricity pricing the cluster generates roughly \$38 in revenue per GPU per hour, which is revenue rather than profit but establishes the economics of the deployment. The ratio between the ceiling and actual volume is the strategic point: if a fraction of one cluster's capacity serves 8 trillion tokens per day, then growth to 20, 50, or 100 trillion per day requires no additional hardware, only additional demand. For context, the disclosed daily volumes reported on a public leaderboard were 180 trillion for ByteDance, about 107 trillion for Google, and about 8.6 trillion for OpenAI's API.

## Reported, circulated, and inferred

The conversation separates three epistemic layers when discussing DeepSeek's next model, and the separation is more useful than any of the claims.

**Reported with reasonable confidence**: Huawei engineers are stationed at DeepSeek's offices, a presence reported in October 2026 and independently described as a permanent liaison team based in Hangzhou, following extensive low-level operator adaptation during the V4 cycle. The framing offered in the conversation is that co-location becomes the product: a chip vendor that embeds engineers in the customer's office is selling integration rather than hardware.

**Circulating as rumour**: that V5 is already pretraining as a roughly 2-trillion-parameter sparse mixture-of-experts model on Ascend 950 and 950DT. The account that documented the claim stated explicitly that nothing was confirmed and that every number should be treated as a repeated claim rather than a reported fact. The parameter count varies by a factor of four across outlets — 2 trillion, 8 trillion, and "5T+" — which is itself evidence of speculation rather than disclosure.

**Better sourced**: a plan to train V5 on Ascend 950, reported by multiple Chinese outlets citing supply-chain sources, with a 2027 timeline and at least 160,000 Ascend 950DT chips at a new data centre in Ulanqab, Inner Mongolia, operational in late 2026 and used initially for inference. An earlier September report stated that no training plan existed yet, so the pretraining framing is a recent escalation rather than a long-standing roadmap.

The reason the rumour is taken seriously is structural rather than evidentiary: pretraining a frontier model from scratch on non-Nvidia silicon is the difficulty threshold that domestic accelerators have not crossed. Inference on Ascend is established; from-zero pretraining is not. If it occurs, its significance rests less in the resulting model than in the demonstration that the operation can be repeated, which erodes the CUDA position at the software layer rather than the silicon layer.

## Halo products and commodity compute

The conversation's recurring economic argument is carried by an automotive analogy that it then qualifies. The YangWang U9 Xtreme, which crossed 503.17 km/h in Abu Dhabi in November 2026, is a halo product: it demonstrates that the industrial base can beat the incumbents at the top of the range. It is not the mechanism by which capability spreads. The mechanism is one tier down, in vehicles such as the Leapmotor Lafa 5 at roughly \$13,100, where the accessible product reaches orders of magnitude more buyers.

Huawei occupies both positions at once. The CloudMatrix 384 supercluster, with 384 Ascend 910C chips, delivers roughly 300 petaflops of BF16 aggregate throughput — more raw throughput than a GB200 NVL72 — at approximately three times the price and nearly four times the power draw, which is the halo strategy of scaling out to a headline number. The Ascend 950PR at roughly 50,000 yuan (about \$7,000) per card, designed for inference and deliberately compatible with CUDA-style software, is the commodity strategy.

The market data tracks the second strategy. Nvidia's share of China's accelerator shipments fell to 34% in the first half of 2026 while Huawei reached 28%, and Chinese accelerators reportedly match Nvidia on price per TFLOP. The qualification the conversation adds is that the "thrills" are not equivalent: driving a fast car is a subjective experience, whereas access to cheap compute is an economic input that determines who can train, serve, and build. The relevant question is whether the software moat delays commoditization long enough for Nvidia to preserve its margins, or whether price convergence is already the leading edge of the same transition.

## Why the peak-FLOPS framing does not address this

Nvidia's marketing is organized around capability and ecosystem: headline FLOPS and bandwidth, NVLink domain size, the CUDA and cuDNN toolchain, the training frontier, and total cost of ownership framed around utilization and reliability. That framing is internally coherent, and the 155-trillion-token figure does not fit inside it, because the figure is a statement about full-stack efficiency — model architecture, inference engine, Ascend kernels, prefill/decode disaggregation, cache design, scheduling — and says nothing about peak throughput.

The conversation offers two reasons the marketing does not compete on that axis. First, it does not need to yet: the position is defended by the training frontier and the ecosystem, where the pitch is that the workload cannot easily be performed elsewhere. Second, the inference-efficiency argument is largely an argument about the software layer, and the hardware layer is where the lead is clearest.

The framing gap does not invalidate the Nvidia position. Frontier training still occurs predominantly on Nvidia hardware, switching costs are real — DeepSeek's own accelerator switch demonstrates that dual-targeting is the pragmatic path rather than that the gap has closed — and reliability and support at scale matter to enterprise buyers in ways benchmarks do not capture. The conclusion is narrower: inference is where the volume is, volume economics are decided by full-stack efficiency rather than peak FLOPS, and the marketing answers a question that buyers impressed by cost per token did not ask.

## "Enough" as a market segment

A related observation in the conversation concerns the scale of demand that frontier hardware does not serve. For an independent developer or a document-processing user, a Flash-tier model at 175 or more tokens per second is not a compromise but surplus to requirement. The frontier solves problems such a user does not have: multi-step reasoning over million-token contexts, or training a base model.

The qualification is that frontier work funds the tier below it. Distillation, architecture research, and training recipes propagate downward, so the frontier program is, in part, research and development for the models that occupy the mid-tier two years later. The benefit therefore arrives indirectly and on a different timescale than the marketing implies.

The user-side data that prompted this discussion came from local token dashboards rather than service disclosures: one published breakdown for October 2026 reports a single user consuming 289 million tokens across 142 sessions and 2,041 model calls, and a WorkBuddy Standard plan at roughly ¥70 per month is estimated to unlock about 2.4 billion tokens including cached tokens at a 96.36% cache hit rate. These are per-user consumption figures; no public figure isolates DeepSeek's aggregate volume attributable to WorkBuddy, so the aggregate attribution remains an inference.

## Export control as a performance threshold

The control regime is not organized around Nvidia. It is organized around Export Control Classification Numbers 3A090 and 4A090, which apply when a chip exceeds a Total Processing Performance threshold. Because the criterion is computational rather than brand-specific, it captures every manufacturer.

AMD's data-center accelerators are named in the rules: the Instinct MI250X, MI300X, and MI325X exceed the thresholds and fall under the same tier as Nvidia's flagship parts. The Bureau of Industry and Security reviews MI325X licences for China case by case, AMD confirmed receiving some licences in early 2026, and the company's chief executive has acknowledged that its highest-end GPUs are subject to the controls. AMD's attempt to design a reduced part for the Chinese market was blocked without a licence, which establishes that downmarket variants are not a route around the regime.

Intel is captured on the same basis: Gaudi has required an export licence for China since April 2025, and the company has been evaluating whether a version of its Crescent Island GPU can be sold there in compliance. Beyond per-chip licensing, the regime includes a 15% revenue share that both Nvidia and AMD agreed to pay on China sales as a licensing condition, a 25% tariff on selected advanced AI chips from both vendors, and rules extending to Chinese-owned subsidiaries located outside China, aimed at preventing advanced parts such as AMD's MI350X from reaching Chinese firms through intermediaries.

## The cost of the control regime to Nvidia

The conversation assembles the cost side of the ledger. Export controls reduced Nvidia's China revenue share from 95% to roughly 9% by fiscal 2026, a decline Nvidia's chief executive described as a policy error. The company booked a \$4.5 billion charge on H20 inventory and a further \$400 million on H200 commitments, and H200 shipments account for under 1% of quarterly data-center revenue.

The compliance burden is expanding rather than contracting. In November 2026 the Commerce Department drafted rules requiring individual export licences for Blackwell and Rubin exports to data centres in seven intermediary countries, including Singapore and Malaysia, with disclosure of all end customers, ongoing compliance audits, and reporting of computing consumption metrics to Washington. Nvidia has also been placed in the position of policing its own customers, telling data-centre operators that at least 51% of their services must go to non-Chinese firms, which restricts the route by which Chinese laboratories rented overseas compute.

The strategic cost is that the allocation regime manufactures competitors. Nvidia's share of China's AI accelerator market fell to 34% in the first half of 2026 while Huawei reached 28%; Nvidia shipped 678,000 accelerators to China in that period, a 44% year-over-year decline, while Huawei shipped 572,000, up from just over 300,000 a year earlier. Beijing has reinforced the shift by requiring state-funded data centres to use domestic chips. The same period saw GPUs converted into a diplomatic instrument: expanded exports offered as part of a peace agreement, access granted to the UAE after a \$1.4 trillion infrastructure pledge, and 18,000 GPUs approved for Saudi Arabia's Humain based on investment and security cooperation.

The analysis in the conversation connects this to the ecosystem argument. The moat is defended by CUDA's depth, but the allocation regime gives Chinese developers a strong incentive to build alternatives, and every restriction increases the maturity of the abstraction layer that makes the hardware substitutable. The stated conclusion is that the policy achieves geopolitical objectives while Nvidia pays for them in market share, revenue predictability, and the long-term integrity of its ecosystem.

## Southeast Asia: hedging as operating logic

The regional response is neither submission nor rejection but diversification of dependencies. The sovereign programmes are concrete: Malaysia launched the ILMU model in August 2025 and proposed roughly USD 496 million for a sovereign AI cloud in its 2026 budget; Vietnam passed an AI law in December 2025 asserting sovereignty over data, infrastructure, and models with a 2030 regional-hub target; Singapore released the SEA-LION models as a strategic capability. The Bangkok Declaration framed control over computing resources as a national right.

The evidence that this is operational rather than declaratory is procurement. Malaysia has been evaluating Huawei's Ascend 910C as the backbone of a MYR 2 billion sovereign cloud despite American warnings, while simultaneously implementing its own export permit regime for US high-performance chips since July 2025 as a way of managing transshipment concerns. The pattern is to comply with the minimum necessary to avoid being cut off while declining to outsource infrastructure decisions.

The pressure is real and increasing. The Commerce Department's draft rules impose individual licences for Blackwell exports to data centres in Malaysia, Thailand, Indonesia, and Singapore; proposed rules would cap the Total Processing Performance available to each country at 790 million between 2025 and 2027; and the fallout from the Nvidia leadership crisis increased scrutiny of Singapore and Malaysia as transshipment points, including proposals to close the remote-access route by which Chinese firms rent compute from overseas data centres. The American framework — Pax Silica and the AI SPARK plan — offers funding and technology access to aligned countries, with a draft warning to 35 nations that they cannot maintain both American and Chinese cooperation mechanisms. The regional answer is to negotiate as a bloc through the Digital Economy Framework Agreement and to keep both suppliers viable.

## The ARM precedent and what it actually teaches

The historical comparison the conversation tests is x86 against ARM, and it rejects the simple version. ARM's mobile dominance was not a surprise: by the mid-2000s it was evident that phones would outsell PCs and that x86 power envelopes were unsuitable for that market. What the x86 incumbents did not foresee was the direction of travel upward, into servers and PCs, and the mechanism by which it occurred.

The blind spot was the business model rather than the instruction set. x86 was merchant silicon: Intel and AMD designed, everyone else bought. ARM licensed, which allowed hyperscalers to design their own parts — Graviton, Axion, Cobalt, Trainium, MTIA — and allowed Apple to integrate vertically. The instruction set was almost incidental; the unlock was that the buyer could become the designer, which the merchant model could not offer without cannibalizing its own vendors.

The measurement also requires care. By unit volume ARM has dominated for more than a decade; by revenue and installed base in PCs and servers, x86 retains the incumbent position. The accurate statement is that ARM won the volume war and now contests the value war.

The transferable lesson is about where competition originates. Incumbents underestimate vertical integration and custom silicon because their moat is built on a merchant model in which vertical integration appears irrational until it succeeds. CUDA is the analogous position: a software ecosystem moat that makes switching expensive. The ARM-style challenge is not a faster chip but hyperscalers and sovereigns building their own stacks, and those challengers do not need to match Nvidia on peak FLOPS — they need adequate performance, a different ownership model, and volume. There is also a technical echo: x86's lock-in operated through binary compatibility, whereas CUDA's operates at source level, where porting is possible but costly. An accelerator switch such as `DEEPINFER_ACCELERATOR` is an attempt to make the hardware an implementation detail, which is how compiler layers historically eroded instruction-set advantages.

## The moving goalposts

The conversation identifies a repeating sequence in Western analysis of Chinese semiconductor capability. First, the constraint was lithography: SMIC cannot obtain EUV and is limited to DUV at 7 nm. The response was advanced packaging, chiplets, stacked dies, and an efficiency argument in which a 95%-efficient inference stack does not require the leading node to win on cost per token. Second, the constraint was memory bandwidth: Huawei shipped proprietary HiBL and HiZQ memory and split the 950 into prefill and decode variants to trade bandwidth against cost. Third, the constraint was CUDA: DeepInfer shipped one codebase with an accelerator switch, TileLang targets both CUTLASS and Ascend, and Huawei embedded engineers in DeepSeek's offices. Fourth, the constraint is from-zero pretraining on domestic silicon, which is the subject of the rumour discussed above.

The next candidates are already visible: advanced packaging and yield at scale, EDA tooling, reliability under sustained production load, and the recurring claim that the capability can be copied but not innovated. Some of these are genuine constraints that will hold for years.

The general observation is about the word "always" in this discourse. Each constraint named as permanent has so far resolved into a specific engineering problem attacked with unusual focus, frequently because export controls removed the option of purchasing the easy solution. The controls have functioned as a forcing function for the co-design work that now produces the efficiency figures. This does not establish parity across the board; it establishes that the appropriate form of the claim is "this gap is real, and here is how long it should be expected to last" rather than "the gap is permanent."

## Nvidia after Huang: front-loaded certainty

Jensen Huang resigned as president, chief executive, and board member on 12 November 2026, following reports about his personal conduct, and the board appointed chief financial officer Colette Kress as interim chief executive while retaining her finance responsibilities. The analytically significant detail is the absence of a named successor or a formal succession plan, a vulnerability that analysts had identified beforehand. The internal candidate most frequently mentioned is Ian Buck, who led the data-center division and is associated with the CUDA lock-in; external names floated included Tim Cook and Lip-Bu Tan. The board was expected to name a permanent successor within three to four months.

The near-term roadmap is the predictable part. Counterpoint Research's assessment is that the roadmap from Blackwell through Vera Rubin is locked and that the engineering organization can sustain execution for 18 to 24 months; Nvidia had already published a roadmap through 2028 covering Blackwell, Rubin, and Feynman, with core directions for GPUs and interconnects specified. The board and the interim chief executive committed that operations, customer commitments, and the product roadmap would continue without interruption, so the systems under discussion — Vera Rubin NVL72, the Rubin CPX racks, BlueField-4, NVLink 6 — are not in immediate jeopardy.

The uncertainty begins after that window. The 18-to-24-month cadence was a founder-driven function rather than an institutional one: Huang set the annual rhythm that pulled foundries, memory suppliers, packaging partners, and hyperscalers onto a shared schedule. Patrick Moorhead's formulation is that the future roadmap has not been defined and that executing the current one requires centralized command decisions. Counterpoint adds a structural risk: Nvidia operated with dozens of senior executives reporting directly to the chief executive and no named successor, so a move to a conventional hierarchy will test the organization as long-tenured lieutenants adjust to new reporting lines and compete for roles.

The transition also bears on the earlier arguments. Counterpoint frames it as giving rivals — AMD and the hyperscaler custom-silicon teams — their best opening in years, and reiterates a forecast that server AI ASICs will overtake GPU unit shipments within the year. The leadership vacuum creates space for sovereign AI agreements and neocloud financing that Huang had personally driven. The conclusion the conversation draws is that the resignation front-loaded the certainty and back-loaded the ambiguity: products are predictable for roughly two years, and the direction after that depends on a chief executive who does not yet hold the role.

## Anthropic's listing

The valuation question has a short answer with a qualification: the current target is achievable, and the target has already moved. Earlier figures reportedly reached \$2 trillion; the company's filing targeted a fully diluted valuation of up to \$1.4 trillion, an implied range of roughly \$1.26 trillion to \$1.41 trillion at \$70 to \$78 per share, with some investors arguing for approximately \$1 trillion.

Demand supports the revised figure. The offering drew roughly six times the orders for the shares available, and bankers were reportedly considering raising the price range above the stated band, which would lift the valuation toward \$1.5 trillion or higher. The business data behind the demand: an annualized revenue run rate of \$81 billion as of late October 2026, up from \$65 billion in July, with a net loss of \$23.3 billion in the September quarter, and a \$26 billion private placement committed by Google, Nvidia, Microsoft, AMD, Broadcom, Micron, and TSMC alongside the offering.

The risks are timing rather than demand. A sector selloff and political headwinds created a window in which investors sought deeper discounts, and the company has the option to delay rather than accept a lower multiple, with \$146.6 billion in cash as of 30 September. The structural exposure is the infrastructure commitment of \$895.4 billion, of which roughly \$69.8 billion falls due in the twelve months after September 2026, with the offering proceeds intended to fund that spending.

The listing was scheduled for Thursday, 19 November 2026 on Nasdaq under the ticker ANT, with the offer period closing at 4:00 p.m. Eastern on Tuesday, 17 November, pricing on the evening of Wednesday, 18 November, and trading beginning the following day.

## Tile abstractions on Nvidia hardware: convergence rather than conflict

The final technical question is whether Nvidia could align its GPUs with tile programming, and the answer is that it is already doing so.

Nvidia's own tile stack consists of **CUDA Tile**, described as a way to program GPUs at a higher level than SIMT; **TileIR**, an array-based sibling to PTX implemented as an MLIR dialect, intended to provide performance portability across hardware generations while retaining architecture-specific features such as tensor cores; and **cuTile**, a Python DSL for portable CUDA kernels in the idiom of NumPy and PyTorch. The direction of travel is upward, toward the abstraction that TileLang advocates.

The relationship is cooperative rather than competitive. On Nvidia hardware, TileLang is a CUDA generator: `T.gemm` dispatches through Nvidia's CUTLASS tile library, and an experimental backend targets the CUTLASS CuTe DSL.

The hardware has also moved in the same direction. Blackwell's tensor memory is a dedicated on-chip space for tensor-core operands with explicit allocation and load/store instructions; the `tcgen05` instruction group manages the lifecycle of TMEM tensors with compiler-planned layout and synchronization; and TileLang already supports transferring data between shared memory and tensor memory.

The CISC-versus-RISC comparison is therefore imprecise. That divide concerned the instruction set, the vocabulary the hardware exposes. The shift from SIMT to tiles concerns the programming model — who is responsible for the schedule — and the two models coexist: CUDA's tile mode imposes restrictions (no inline PTX, no `threadIdx` access) but is an additional layer rather than a replacement. The closer analogy is the move from assembly to C, or from CUDA C to a Python DSL: the hardware executes the same instructions, and the compiler assumes responsibility for scheduling. The open question is not compatibility but ownership: whether Nvidia's proprietary tile stack becomes the default path before open alternatives such as TileLang become the portable standard.

## Diffusion in China

The claim that AI diffusion would be limited by political constraints did not survive the data. By the first half of 2026 China's generative AI user base exceeded 700 million people, a penetration rate above 50%, meaning roughly one in two people. Usage is not shallow: 76% use these systems for question answering, and usage of AI office and efficiency tools grew by more than 100% year over year.

Enterprise adoption followed the same path. The share of firms that had moved past the pilot stage of advanced AI deployment rose from 46% to 88% in a single year; adoption among large and mid-sized enterprises reached 81.3% in the first quarter of 2026 against 20.7% in 2023; and 93% of executives planned to increase AI investment in 2026.

The diffusion was cultural as well as corporate. On Douyin, AI-generated pet videos accumulated more than 3.1 billion views from over 160,000 creators, and ByteDance's Doubao assistant logged 1.9 billion interactions in a single day during the Spring Festival period. The mechanism was the one that carried mobile payments and short video: integration into super-apps, low cost, and immediate utility.

The qualification is that adoption is not transformation. Accenture's data shows the share of firms reporting significant productivity, revenue, or profit gains rising only from 9% to 14%, and a separate analysis finds more than half of listed companies still on the left side of the J-curve, with AI-related value creation not yet offsetting disruption to legacy business. The diffusion assumption failed; the value-capture assumption remains open.

## The unglamorous deployments: customs and procurement

The argument that follows from this observation is that the value of Chinese AI deployment is more visible in process integrity than in reported productivity. Two documented domains support it.

**Customs.** In export lithium-battery packaging inspection, image recognition and algorithms reduced verification time from 48 hours to under 30 minutes without manual on-site inspection; for CATL, the smart packaging supervision model cut shipping cycles from 15 days to 10 days and raised capacity utilization from 70% to 95%. Guangzhou Customs deployed "digital customs officers" — agents that pre-screen declarations for prohibited or restricted goods before submission, with big-data models cross-checking declared information against physical data afterwards. A logistics manager reported that document review which previously took days now takes minutes, and uninspected cross-border parcels clear in as little as 16 minutes.

**Procurement integrity.** The discipline inspection team at the General Administration of Customs built 65 risk-screening models across 25 checkpoints in the bidding process — pre-bid, bid, and post-bid — covering more than 40,000 projects nationwide, screening for exclusionary tender documents, anomalous expert scoring, bid rigging, and irregular selection of procurement method; one screening round flagged nine projects with elevated integrity risk. Nationally, the systems corrected 19,000 discriminatory clauses and identified more than 3,000 leads on collusive bidding. In Anhui, a model trained on 290 regulatory documents and 82.9 terabytes of historical tender data audited 36,000 documents, flagged 3,264 questionable clauses, and contributed to 324 collusion cases; in one sewer project it identified 456 matching passages, 101 identical images, and 44 shared typographical errors between two bids presented as independent.

The analytical distinction is between output-oriented and capability-oriented measures. A customs declaration that clears in 16 minutes is not a productivity gain in a profit-and-loss line; it is a reduction in warehousing cost, working-capital lock-up, and opportunities for rent-seeking at the border. A model that flags anomalous scoring is a deterrent that raises the expected cost of collusion before any case is brought. Both appear as avoided losses, reduced friction, or deterrence rather than as new revenue, so an output-oriented framework systematically undercounts them.

## Legibility and attention

The reason this work is underweighted is structural. Frontier training runs are legible to the institutions that allocate attention: a large model trained on a named cluster produces a press release, a benchmark table, a valuation narrative, and a capital-expenditure justification. A procurement model trained on 82.9 terabytes of tender documents produces 324 resolved cases, which is institutionally significant and narratively invisible: it does not move a share price, does not appear on a leaderboard, and has no vendor marketing organization behind it.

The feedback loop runs in one direction. Frontier scale justifies capital expenditure, which justifies valuation, which justifies coverage, which reinforces the premise that frontier scale defines the frontier. The applied deployments have no equivalent loop; they operate quietly.

The consequences extend beyond media. Policymakers who see only frontier benchmarks underweight deployment capability, and the export-control debate is almost entirely about training capability — performance thresholds, FLOPS limits, cluster sizes — and almost not at all about diffusion capability. Investors who see only frontier valuations underprice applied work. Analysts who measure only productivity gains miss value that appears as reduced corruption, faster clearance, and hardened processes.

The necessary caveat is that the two are complementary rather than substitutable. Procurement models run on fine-tuned or distilled base models, and frontier training produces the architectures, distillation recipes, and efficiency techniques that make specialized deployment cheap enough to be widespread. The frontier is the research laboratory and the applied deployments are the factory floor; the laboratory receives the coverage and the factory floor produces the output.

## The mathematics episode and the verification bottleneck

The final subject is the reception of OpenAI's October 2026 mathematics release, which the conversation treats as a case study in a recurring pattern. On 6 October 2026 OpenAI released more than 700 AI-generated mathematical manuscripts claiming results on at least 372 open problems, including a partial attack on the Navier–Stokes Millennium Prize problem.

The verification record is the substantive part. Of 722 manuscripts, about 162 were fully checked in the Lean theorem prover; only 10 of 719 included the model's chain of thought; 42% had not been formalized at all; and three were withdrawn because of errors. The Association for Human Mathematics, in a statement resurfaced and effectively endorsed by Terence Tao, rejected the framing: "Releasing over 700 files at once is not a demonstration of scholarship, but a demonstration of power." Melanie Wood described the scientific status plainly: at the point of release there is no human understanding of the results, and the work of understanding begins afterwards.

The civilizational claim attached to the release did not originate with the AI companies. It originated in a thought experiment by Tao about verification: whether a drug discovered by an AI would be accepted if no human understood why it worked. The question concerns the gap between a true result and an understood one. The public response converted it into a claim that mathematical results imply cures for cancer and the end of hunger.

The structural reading is a shift in the bottleneck rather than an expansion of capability. Producing candidate proofs is no longer the constraint; verifying, understanding, and building on them is. Tao's argument concerns absorbability: results that arrive faster than a field can digest them do not automatically benefit the field, because the field depends on methods, connections, and the training of the next generation. Timothy Gowers framed the risk as ending up with a powerful tool that no one is able to master, because the incentive to spend years acquiring the expertise to read machine output erodes.

The historical parallel is the expert-systems boom of the 1980s: a genuine technical advance, a wave of claims about general transformation, and a contraction when the systems proved expensive, rigid, and difficult to scale — followed by a funding winter that affected the research agenda as well as investment. The current technology is more general and more capable, but the mechanism by which a narrow result is projected onto civilizational problems is the same, and the projection performs the work that the evidence has not.

## What the conversation establishes

Read together, the arguments converge on a single claim with several independent supports. The capacity to produce frontier-scale compute is no longer the binding constraint on the diffusion of AI capability; the binding constraints are the efficiency of the software stack, the cost of a token, the institutional capacity to absorb results, and the political structures that govern distribution. The 155-trillion-token figure is a statement about the first; the ~8 trillion consumption figure, the \$0.60 per million token price, and the 175-token-per-second generation rate are statements about the second; the 14% value-realization figure and the Lean verification backlog are statements about the third; and the export-control regime, the Ascend product split, and the Southeast Asian hedging strategy are statements about the fourth.

The two organizations at the centre of the conversation are positioned on opposite sides of that shift. Nvidia's advantage is concentrated in capability, ecosystem, and the training frontier, defended by a software moat and a product cadence that was personally maintained by a chief executive who has now departed. DeepSeek's and Huawei's advantage is concentrated in full-stack efficiency at the inference layer, demonstrated on hardware that the control regime was designed to make unavailable. Neither position is secure: the first depends on institutionalizing a founder's cadence while the competitive axis moves beneath it, and the second depends on whether from-zero pretraining on domestic silicon crosses from rumour to demonstrated capability.

The observation that organizes the rest is about what becomes visible. The frontier produces legible artifacts — benchmarks, valuations, press releases — while the deployments that change institutional behaviour produce case counts and clearance times. A control regime, a marketing organization, and an attention market all optimize for the legible artifact. The parts of the transition that are least visible are, on this account, the parts where the diffusion is actually occurring.

## Sources

The conversation cited the following primary material. Links are grouped by subject and reproduce the citations from the transcript.

**Programming models and compilers**

- [The map, the lab, and the method (accelerator tutorial)](https://accelerator-tutorial.pages.dev/part-0/00-the-map-the-lab-and-the-method/)
- [TileLang target list](https://github.com/tile-ai/tilelang/blob/210611dca01198cacac9a02103c2a95e18cf6375/docs/get_started/targets.md)
- [TileLang installation requirements](https://tilelang.com/get_started/Installation.html)
- [CUDA Tile documentation](https://github.com/nvidia/cccl/blob/5d63af4077b8ae9c569d55428cb2cdc8ebbc31a5/docs/libcudacxx/tile.rst)
- [TileIR and cuTile (ARRAY 2026)](https://pldi26.sigplan.org/details/ARRAY-2026-papers/14/)
- [tcgen05 copy primitives (TVM)](https://tvm.apache.org/docs/tirx/tile_primitives/copy_async/tcgen05_cp.html)
- [Blackwell TMEM (LLVM dev meeting)](https://llvm.org/devmtg/2025-04/slides/technical_talk/ozen_blackwell.pdf)

**Accelerator hardware**

- [Apple Neural Engine programming](https://deepwiki.com/hollance/neural-engine/6.2-programming-the-ane)
- [ANE reverse engineering](https://raw.githubusercontent.com/eiln/eiln.github.io/main/posts/ane.html)
- [Blackwell memory architecture](https://www.freecodecamp.org/news/the-evolution-of-nvidia-blackwell-gpu-memory-architecture/)
- [Nvidia RTX Spark](https://www.engadget.com/2184558/nvidia-rtx-spark-chip-windows-pcs/)
- [Ascend 950PR specification](https://atii.edu-sjtu.cn/article/10247)
- [Ascend 950 PR/DT split](https://www.eet-china.com/mp/a502367.html)
- [Vera Rubin platform](https://www.nvidia.com/en-in/data-center/technologies/rubin/)
- [Vera CPU performance tuning guide](https://docs.nvidia.com/dccpu/vera-mn-perf-tuning-guide/overview.html)
- [Rubin CPX rack](https://tech.yahoo.com/ai/articles/nvidia-unveils-rubin-cpx-gpu-204700593.html)
- [AI GPU pricing](https://amnic.com/blogs/ai-gpu-pricing)

**DeepSeek and Huawei**

- [DeepInfer open-source release](https://tech.yahoo.com/ai/articles/deepseek-open-sourced-engine-runs-200250940.html)
- [FlashMLA for Ascend 950](https://pypi.org/project/deepinfer-flashmla/1.0.0/)
- [DeepSeek–Huawei open-source tools](https://tech.yahoo.com/ai/articles/deepseek-huawei-release-open-source-140000251.html)
- [DeepInfer deployment analysis (36Kr)](https://eu.36kr.com/en/p/4034049305973891)
- [DeepInfer cache and storage](https://techorange.com/2026/10/21/deepseek-deepinfer-ai/)
- [Token throughput leaderboard](https://www.linkedin.com/posts/david-ouyang-94405b23_ai-datavisualization-buildinpublic-activity-7517681627175628800-T4Xd)
- [DeepSeek API pricing in Malaysia](https://bigdomain.my/tokenhub/)
- [V5 pretraining rumour](https://news.abnasia.org/blog/posts/en-deepseek-v5-ascend-rumor-7712)
- [160,000 Ascend 950DT deployment](https://dataconomy.com/2026/11/04/deepseek-plans-to-train-v5-using-160000-huawei-chips/)

**Export control and geopolitics**

- [BIS advanced computing controls](https://trembachlaw.com/article/bis-advanced-computing-chip-export-controls-entity-list-california-march-2026)
- [Commerce licence review policy](https://www.bis.gov/press-release/department-commerce-revises-license-review-policy-semiconductors-exported-china)
- [Nvidia and AMD revenue-sharing arrangement](https://www.sdxcentral.com/news/nvidia-amd-agree-to-pay-us-govt-15-of-china-chip-sales-for-export-permissions-report/)
- [Nvidia China revenue decline](https://www.ainvest.com/news/nvidia-briefing-isn-losing-china-sales-channels-left-2611/)
- [Licensing across seven intermediary countries](https://eastasiabrief.com/trade-policy/us-expands-ai-chip-licensing-data-centers-across-seven-1364)
- [China accelerator market share](https://economictimes.indiatimes.com/tech/artificial-intelligence/nvidias-china-ai-chip-share-falls-as-huawei-closes-gap-report-finds/printarticle/134907732.cms)
- [Compute commoditization (GlobalData)](https://www.globaldata.com/newsletter/details/us-political-shift-and-nvidia-curbs-push-ai-compute-towards-china_404811/)
- [Southeast Asian sovereign AI](https://fulcrum.sg/article/commentaries/advancing-southeast-asias-ai-future-through-sovereign-ai-models/)
- [Malaysia evaluating Ascend 910C](https://ciosea.economictimes.indiatimes.com/news/data-center/malaysia-weighs-huawei-chips-for-sovereign-ai-cloud/133960841)
- [ASEAN hedging and Pax Silica](https://asiapolicy.asiasociety.org/p/asean-hedges-with-pax-silica)

**Nvidia leadership**

- [Nvidia chief executive transition](https://nvidianews.nvidia.com/news/nvidia-announces-ceo-transition)
- [Roadmap after the resignation](https://www.datacenterknowledge.com/data-center-chips/huang-resigns-nvidia-s-ai-infrastructure-roadmap-in-question)
- [Counterpoint analysis](https://counterpointresearch.com/cn/insights/losing-the-jensen-beat)

**Anthropic**

- [IPO price band](https://www.ndtvprofit.com/markets/anthropic-sets-ipo-price-band-at-70-78-per-share-targets-up-to-64-4-billion-raise-at-1-trillion-valuation-12308288)
- [Sixfold oversubscription](https://www.thehindubusinessline.com/markets/anthropic-ipo-draws-sixfold-demand-targets-14-trillion-valuation/article71696359.ece)
- [Listing date](https://sg.finance.yahoo.com/news/anthropic-sets-ipo-date-for-thursday-nov-19-173011206.html)

**Diffusion in China**

- [Generative AI user base](https://finance.sina.com.cn/wm/2026-10-05/doc-iniueriz4265144.shtml)
- [Enterprise adoption](http://www.jingjiribao.cn/static/detail.jsp?id=670217)
- [AI-generated pet videos](http://peopleschina.com/zzjj/202611/t20261109_800450687.html)
- [Customs automation](https://www.toutiao.com/article/7706105598437425690/)
- [Procurement screening at scale](https://legal.gmw.cn/2026-01/20/content_38547478.htm)
- [Anhui procurement model](http://en.people.cn/n3/2026/0613/c90000-20467127.html)

**Mathematics**

- [OpenAI mathematics release](https://techcrunch.com/2026/10/08/openais-math-solutions-arent-meeting-the-fields-standards-yet/)
- [Mathematicians' response](https://futurism.com/artificial-intelligence/mathematicians-openai-furious)
- [Tao on proof and evidence](https://easyainews.com/en/longform/terence-tao-ai-proof-evidence/)
