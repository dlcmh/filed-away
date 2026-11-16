# TileLang, Flash Attention, and the durability of the CUDA moat

> A thematic reorganization of a conversation on Apple Silicon kernel coverage, the AnimateDiff blind spot, and whether accelerator software lock-in can survive the abstraction layer.

> Source: [shared conversation](https://chat.deepseek.com/share/yy6cfsl7nlbuf96yqa) on chat.deepseek.com. 8 questions, 8 answers. The source link expires when the conversation is deleted from DeepSeek. This note reorganizes the conversation by subject rather than by turn; claims and figures are those of the conversation and its cited sources, dated November 2026.

The conversation starts from a practical question about a local laptop and ends on the structure of the accelerator market. The chain is worth following, because each step narrows the gap between "software problem" and "hardware problem" until only a specific class of work remains genuinely hardware-bound. The sequence runs: when a tile compiler is worth using on Apple Silicon at all, why one particular video architecture fails despite that, what Flash Attention is and which implementations of it exist, why the absence of a CUDA binary does not make an algorithm unavailable, which limits are actually architectural, and what the resulting contest for the CUDA position looks like.

## When a tile compiler is worth the trouble

For stock PyTorch operations on an M5 MacBook Pro, the default is PyTorch's MPS backend, and the conversation is explicit that TileLang is not a replacement for it. "Optimized" in the MPS case means operator-level optimization: PyTorch supplies fast implementations of the operators it ships. It does not supply a tile-level programming model for expressing a new fused operator.

The gap that TileLang addresses is therefore not a general performance gap but a coverage gap. MPS has limits, and an unsupported operation can fall back to the CPU, which forces transfers and synchronization; advanced indexing, unusual data types, and custom operators are the common cases. A single fallback inside a hot loop can dominate the runtime. A TileLang kernel placed behind a PyTorch custom operator keeps the work on the GPU instead.

The cases where that matters are specific:

- an operator for which MPS has no adequate kernel, or one that falls back to the CPU;
- cross-operator fusion that eager PyTorch will not perform, such as a GEMM combined with activation and normalization, dequantized GEMM, or a custom attention variant;
- a single kernel codebase that targets both Metal and CUDA rather than separate implementations;
- access to M5-specific GPU features, since the Metal backend has been adding cooperative-tensor support for `T.gemm` with a simdgroup fallback for unsupported shapes.

The MPS ecosystem itself endorses the narrow version of this position. vLLM's MPS guidance advises that when an operation has no suitable implementation, the first step is to reuse a shared Metal kernel, and otherwise to write a small TileLang kernel behind the same hook, after profiling and after evaluating PyTorch compilation for fusion.

Two measurements keep the recommendation bounded. On the current Metal backend a full-tile fp16 GEMM runs about 5–6% behind PyTorch MPS on the M5 and at or slightly above MLX, so a standard dense GEMM is not a reason to adopt TileLang. A naive TileLang LayerNorm has been measured more than 300× slower than the PyTorch baseline, which indicates how strongly kernel performance depends on how the kernel is written. The practical rule that follows is: PyTorch MPS as the default, profile first, and treat TileLang as a surgical tool behind a custom operator when a concrete kernel-level gap has been identified.

## The AnimateDiff case and the missing kernel

The conversation then examines a quoted comparison claiming that a 16-frame AnimateDiff clip on MPS takes 2–3 minutes, that Core ML conversion fails or degrades on the motion modules, that MLX has no port, and that the ANE is unreachable. The assessment is that the four failure modes are accurate, and that the timing figure understates the cost: a 16-frame, 10-step run on an M2 Max has been measured at roughly 66 minutes, with individual steps taking 200–334 seconds. The discrepancy between the quoted 2–3 minutes and the measured 66 minutes is worth noting rather than reconciling; the qualitative conclusion does not depend on it.

The root cause is not insufficient GPU throughput. AnimateDiff's temporal attention requires Flash Attention to be tractable, and MPS does not provide a Flash Attention implementation. Each step materializes the full key-value cache for all 16 frames, and cost grows with frame count. CUDA has the optimization; MPS does not, and that single absence accounts for most of the gap.

TileLang is technically relevant and does not solve the problem by itself. It can target Metal, and it contains attention examples including block-causal attention for diffusion models, so a fused temporal-attention kernel that avoids materializing the full cache could in principle be written and exposed as a PyTorch custom operator. Three constraints apply:

1. No ready-made AnimateDiff kernel exists. TileLang provides the language for writing one, not the kernel.
2. The Metal backend is younger and less mature than the CUDA backend; performance portability from CUDA examples is not guaranteed.
3. The bottleneck is architectural as well as linguistic. The motion modules are unusual temporal-attention layers with specific reshaping and injection points, so a correct and fast Metal implementation is a project.

The surrounding ecosystem also argues against generalizing from this case. MLX ports exist for LTX-Video and LongCat-Video-Avatar, and FastVideo has brought accelerated video generation to Apple Silicon through MLX. In the same benchmark, Wan2.1 used as an AnimateDiff replacement ran 17 frames in about 220 seconds on the same Mac Studio, roughly 18× faster than the AnimateDiff baseline, and a 20-billion-parameter video diffusion transformer has been run end to end on Apple Silicon through MLX, albeit slowly. The pattern is that a model with a native MLX port or a clean MPS path is workable, while a model that depends on an architecture which only CUDA Flash Attention makes fast is not. AnimateDiff belongs to the second category.

## Flash Attention: an algorithm before it was a kernel

Flash Attention was introduced by a Stanford group led by Tri Dao, with Daniel Y. Fu, Stefano Ermon, Atri Rudra, and Christopher Ré as co-authors. It appeared at a workshop in July 2022 and was published at NeurIPS in December 2022. The contribution was to make attention IO-aware: the algorithm manages reads and writes between the GPU's on-chip SRAM and high-bandwidth memory explicitly, which speeds up the computation without changing its result.

That framing matters for everything that follows. The technique is a tiling and scheduling strategy for a memory hierarchy, not a property of a particular instruction set. The original paper shipped with a custom CUDA kernel because that was the hardware on which the memory hierarchy could be exploited, and the reference implementation in `Dao-AILab/flash-attention` has continued through several generations:

| Generation | Location | Language and target | Status |
| --- | --- | --- | --- |
| FA2 | `csrc/flash_attn/src/` | CUDA C++ with CUTLASS 2.x, SM80 and later | Stable, main pip distribution |
| FA3 | `hopper/` | CUDA C++ with CUTLASS 3.x (CuTe), SM90 | Beta |
| FA4 | `flash_attn/cute/` | Python with CuTeDSL, JIT to PTX or CUBIN, SM90 and SM100 | Active development, `flash-attn-4` |

FA2 is the stable workhorse; FA3 rebuilt the kernel around Hopper's asynchronous TMA and WGMMA and added FP8; FA4 moves to a Python-embedded DSL that still compiles to PTX. A Triton reference implementation in the same repository is easier to read and serves as a teaching and AMD path.

## The mistaken inference: an algorithm is not a binary

The conversation rejects the inference that a language model using Flash Attention therefore cannot run on an M5 MacBook Pro. What cannot run is the specific CUDA binary; the algorithm has several implementations for Apple silicon.

- **MLX.** The `mlx-mfa` package provides Metal Flash Attention as a drop-in replacement for `mx.fast.scaled_dot_product_attention`, with causal attention measured at 1.5–2.9× faster than SDPA on Apple silicon. It supports sliding-window, block-sparse, grouped-query attention, RoPE, ALiBi, and int8 SageAttention.
- **PyTorch MPS.** Recent builds from the 2.13 nightlies onward ship a flash-attention SDPA kernel for MPS. Separately, `mps-flash-attn` provides O(N)-memory Flash Attention for MPS with 2–5× faster forward passes than PyTorch SDPA and full gradient support.
- **M5-specific kernels.** `mtlflashattn` uses Apple's TensorOps and neural accelerators and runs 3–11× faster than the stock fused MPS SDPA, while also correcting the stock implementation's numerical divergence beyond roughly 4,000 tokens.
- **llama.cpp.** The Metal backend has native Flash Attention kernels (`FLASH_ATTN_EXT`), with continuing work on per-device tuned kernels and F16 key-value caches.

The CUDA implementation remains the reference and the fastest path. The Apple implementations are younger, and coverage lags for some features: `mtlflashattn`, for example, raises `NotImplementedError` for dropout, backward passes, and head dimensions above 128 rather than returning an incorrect result. The accurate formulation is that a model requiring Flash Attention can run on an M5 through an MLX, MPS, or llama.cpp Metal implementation, provided it is routed through one of those backends. The AnimateDiff case is a model-level gap — an architecture without a maintained Apple silicon port — rather than a hardware-level impossibility.

## Software gaps and hardware ceilings

The general observation offered in the conversation is that AI gaps on Apple hardware are more a function of software availability than of the hardware, and the reply separates the part that holds from the part that needs care.

The part that holds concerns local inference on a single machine, where the binding constraint is usually software. The Flash Attention sequence is the evidence: the hardware executes a tiled, IO-aware attention kernel without difficulty, and what was missing was the Metal or MLX implementation. Once the packages landed, models that could not run began to run. Unified memory is a genuine architectural advantage in this setting, since a large model fits in one address space without PCIe transfers, and software maturity is only now exploiting it.

The part that needs care is that the software gap is itself partly a consequence of hardware and market structure. The CUDA position exists because Nvidia spent fifteen years building it, and that investment follows installed base, so the gap is expensive to replicate and vendors rationally deprioritize a smaller platform. Describing it as "only software" understates its durability.

Beyond that, four limits are architectural rather than conventional:

- **Memory bandwidth.** The M5 provides roughly 150–300 GB/s against about 3 TB/s of HBM3 on an H100. For memory-bound decoding, that ratio bounds tokens per second independently of kernel quality.
- **No HBM and no NVLink.** Single-machine inference is served well; multi-GPU training and very large model serving are not.
- **The ANE is closed.** General kernels cannot be written for it in the way they can for CUDA tensor cores, so the unreachability of the ANE for AnimateDiff is a programming-model limitation rather than a missing library.
- **No tensor-core-equivalent programming model** with the maturity of WGMMA and TMA. Apple's TensorOps, neural accelerators, and cooperative tensors are narrowing the difference but are recent.

The resulting split is that local inference is mostly a software problem and is closing quickly, while frontier training and large-scale serving are genuinely hardware-bound.

## Breaking the moat: the abstraction layer and the Ascend strategy

The CUDA position is not a permanent invariant, and it will not disappear on a convenient timeline. What the conversation describes in China is a two-track strategy that could make the moat irrelevant in one market before it is breached globally.

The first track is the abstraction layer, which moves the programming model above CUDA. Triton has become a genuine accelerator-agnostic alternative, and MLIR has reduced compiler work that once took years to a repeatable process. The concrete example is Modular's MAX platform, which compiles PyTorch-like Python through MLIR and targets CUDA, ROCm, TPU, Trainium, Groq, Cerebras, and Apple silicon at 85–95% of vendor-native performance without vendor-specific code. If that margin continues to close, the economic argument for renting Nvidia hardware because rewriting in CUDA is too expensive weakens.

Huawei's corresponding move is not to force Ascend-native kernels but to deepen collaboration with Triton, PyTorch, vLLM, and verl, contributing upstream so that developers keep the open-source stack. The strategy is to let the abstraction layer perform the porting.

The second track attacks the moat from three directions at once:

- **Hardware compatibility.** The Ascend 950PR is explicitly designed for high CUDA compatibility in order to lower the engineering cost of migration.
- **Software open source.** CANN was fully open-sourced; by the end of 2025 more than 30 community projects were hosted on AtomGit with over 1,500 internal and external developers, and Huawei committed an annual investment of 1,500 PFLOPS of compute and 30,000 development boards to seed the ecosystem.
- **System-scale substitution.** Rather than competing on single-chip performance — the Ascend 910C delivers roughly 60% of an H100's inference performance — Huawei positions CloudMatrix 384, which connects 384 chips and claims about 300 petaflops against roughly 180 petaflops for a GB200 NVL72, with 3.6× the aggregate memory and 2.1× the memory bandwidth, at approximately four times the power consumption. The next-generation Ascend 920C targets more than 900 TFLOPS in BF16 and 4,000 GB/s of HBM3, with 30–40% better training efficiency than the 910C.

The counterweight is that migration cost is not a one-time compiler problem. Engineers report that moving existing workflows to Ascend can require extensive code rewrites and raise time and cost by at least 50%. The difficulty is not in the mainstream operators but in long-tail operator coverage and the custom-kernel development loop: a model that depends on a CUDA extension with no CANN port requires the kernel to be written by hand, and neither TileLang nor Triton necessarily removes that work. The fourfold power penalty is also structural for anyone paying for electricity at scale, and export controls keep Huawei out of the most advanced fabrication nodes, which shapes the cadence of future generations.

The plausible trajectory is regional bifurcation. In China, policy pressure, CANN's open-source momentum, and system-scale clusters can produce a captive but functional domestic stack that does not need to beat CUDA globally to succeed. Globally, Triton, MLIR, and Modular erode the developer-velocity advantage even if Nvidia retains the performance advantage at the frontier. The variable to watch is not whether Ascend overtakes CUDA at the single-kernel level, which is unlikely in the near term, but whether the abstraction layer becomes good enough that the choice of silicon stops being a software decision.

## Why the operating-system analogy only partly holds

The comparison offered at the end is that the outcome may resemble the Windows–macOS or iOS–Android duopoly. The China case already resembles one precedent: Android's open core alongside a de-Googled Chinese fork is roughly what CANN plus Triton could become, a captive but functional domestic stack that does not need to win globally.

The analogy fails on one structural point. Operating-system positions are long-tail positions: Windows and iOS are sticky because millions of applications target their APIs, and the switching cost lives in that long tail. AI hardware behaves differently, because roughly 90% of inference value concentrates in a handful of kernels — GEMM, attention, mixture-of-experts routing, and a few normalizations. A challenger does not need a million applications; it needs perhaps twenty kernels to be competitive on the workloads that generate revenue. That is why Triton and MLIR ports are tractable, and why the position is more contestable than an operating-system duopoly implies.

The same structure explains where the lock-in survives. The long tail is where research and custom operators live: novel architectures, fused experimental layers, one-off kernels. That is where CUDA retains a decisive advantage, and the position therefore migrates from the deployment loop to the research loop rather than vanishing. Deployment commoditizes first; the frontier stays sticky longer.

A clean duopoly is also unlikely, because hyperscaler silicon is a third pole that neither Nvidia nor Ascend absorbs. TPU, Trainium, MTIA, and Maia belong to buyers with both the volume and the incentive to build their own, and they are already doing so. The likely shape is an oligopoly with a shared compiler layer above it, and that compiler layer is precisely what a duopoly would prevent.

Finally, the bifurcation is politically constructed rather than market-evolved. Windows and macOS competed in a single market; what is forming resembles commercial aerospace or telecommunications equipment, with high capital requirements, long cycles, state backing, and export controls performing the market segmentation that competition would otherwise perform. That makes the division durable in a way organic competition would not be, while placing its boundaries under policy control rather than developer preference.

## What the conversation establishes

Three conclusions survive the sequence. The first is that the software gap on Apple silicon is real and is closing, but it is closing within a class of work: local inference, where unified memory and a maturing kernel ecosystem are sufficient. The second is that the remaining hardware constraints — bandwidth, interconnect, and a closed neural engine — bound what software can achieve regardless of kernel quality, so the observation that the gap is mostly software should not be extended to frontier training or large-scale serving.

The third concerns the moat. The contest is not being fought kernel for kernel. It is being fought at the abstraction layer and at system scale, with Triton, MLIR, and Modular on one side and CANN, CloudMatrix, and a deliberately CUDA-compatible Ascend part on the other. The operating-system comparison captures the durability of the resulting division but not its shape: a market stratified into a frontier segment that remains sticky, a commoditized margin where a small number of kernels suffices, and regional silos in between, with a compiler layer thin enough that porting is expensive but not prohibitive.

## Sources

**TileLang and the MPS backend**

- [TileLang project](https://tilelang.com/)
- [TileLang matmul operator reference](https://tilelang.com/deeplearning_operators/matmul.html)
- [TileLang Metal backend development](https://tilelang.com/compiler_internals/metal_tilelang_development.html)
- [vLLM Metal and PyTorch MPS guidance](https://docs.vllm.ai/projects/vllm-metal/en/stable/pytorch-mps/)
- [Apple silicon execution paths compared](https://dev.to/shaktitiwari/apple-silicon-ml-execution-paths-explained-mps-coreml-mlx-and-the-neural-engine-486o)
- [TileLang benchmark paper](https://arxiv.org/html/2607.04454v1)

**Video generation on Apple silicon**

- [AnimateDiff and Wan2.1 timings](https://note.com/claute_colo0514/n/na4ec19b73edd)
- [Video model feasibility matrix](https://github.com/sceneworks/sceneworks/blob/d3f7b05bf22826e44fd43da19cff0985fb17d68b/documents/VIDEO_MODEL_FEASIBILITY_MATRIX.md)
- [LongCat-Video-Avatar on MLX](https://github.com/xocialize/longcat-avatar-mlx)
- [FastVideo on Apple silicon](https://haoailab.com/blogs/fasth3-local/)
- [20B video diffusion transformer on MLX](https://zenodo.org/records/23484926)

**Flash Attention**

- [FlashAttention paper](https://proceedings.neurips.cc/paper_files/paper/2022/file/67d57c32e20fd0a7a302cb81d36e40d5-Supplemental-Conference.pdf)
- [Flash Attention implementation survey](https://raw.githubusercontent.com/llm-infra-atlas/llm-infra-atlas.github.io/refs/heads/main/docs/attention/fa/README.md)
- [Efficient attention kernels lecture](http://www.cs.cmu.edu/~mgormley/courses/10423-f24//slides/lecture18-efficient-ink.pdf)
- [`mlx-mfa`](https://pypi.org/project/mlx-mfa/2.5.1/)
- [`mps-flash-attn`](https://pypi.org/project/mps-flash-attn/0.1.11/)
- [`mtlflashattn`](https://pypi.org/project/mtlflashattn/)
- [llama.cpp Metal Flash Attention release](https://github.com/ggml-org/llama.cpp/releases/tag/b11362)

**The abstraction layer and Huawei**

- [Custom silicon and AI hardware survey](https://github.com/hernanda-git/ai-knowledge-library/blob/main/02-LLMs/08-Custom-Silicon-and-AI-Hardware-2026.md)
- [A compiler and optimized library stack](https://dl.acm.org/doi/pdf/10.1145/3797905.3800551)
- [Huawei open-source collaboration](https://www.huawei.com/en/news/2025/9/hc-shengten-opensource)
- [CANN ecosystem scale](https://article.pchome.net/info/9462.html)
- [CloudMatrix 384](https://www.sdxcentral.com/news/huawei-looks-to-take-on-nvidia-with-rival-cloudmatrix-ai-servers/)
- [Ascend 920C](https://www.techpowerup.com/news-tags/Ascend%20920C)
- [Ascend 950PR compatibility](https://technews.tw/ai-agent/chinese-customers-are-abandoning-huaweis-ascend-and-rushing-to-buy-rtx-pro-5500/43827/)
- [Migration cost and dependency](https://www.digitaltoday.co.kr/en/view/91783/chinas-top-ai-still-dependent-on-nvidia-why-shift-to-domestic-chips-is-slowing)
- [Huawei Ascend hardware overview](https://www.clarigital.com/hardware/ai-chips/huawei-ascend/)
