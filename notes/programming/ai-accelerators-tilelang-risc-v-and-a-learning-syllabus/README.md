# AI accelerators, TileLang, RISC-V, and a learning syllabus

> A DeepSeek transcript on CUDA's moat, C++ demand, accelerator skills, Apple ANE access, affordable accelerator hardware, and a self-study syllabus
>
> Source: [shared conversation](https://chat.deepseek.com/share/kvtkc1cnhbtotkjx10) on chat.deepseek.com. 13 questions, 13 answers. The source link expires when the conversation is deleted from DeepSeek.
>
> Recovered from the shared-conversation HTML export: web citations preserved. Chinese terms are annotated with pinyin and an English translation.

---

## User

CUDA moat will diminish in strength? “Finally, Nvidia's perceived importance for the American ecosystem has been undermined by the very progress in AI. OpenAI can just up and make Jalapeno that is at the very least competitive with Blackwell, at Gen 1; Anthropic will also design a great chip; TPUs are awesome, Meta and Amazon are improving. Broadcom et al. are enough to maintain the supply chain integrity. AIs can write superhuman kernels (Wenfeng also makes this point) and at this rate the CUDA moat will not last except for bespoke hobbyist experiments (every serious lab is now capable of building a better stack for their large scale workloads). On top of it all, Rubin ramp is slower than expected, troubled, and worryingly dependent on Chinese suppliers.”

---

## DeepSeek

The premise you outline captures a real and mounting set of pressures on Nvidia's CUDA moat, but the conclusion that it "will not last" likely overstates the speed and completeness of the erosion. The credible threats are concentrated in **inference** and among a handful of **hyperscale labs**, while CUDA's deepest defenses—verification tooling and training lock-in—remain largely intact.

### 🎯 The Credible Threats: Custom Silicon Is Real

The claim that "every serious lab is now capable of building a better stack" is directionally supported, particularly for inference.

**OpenAI's Jalapeño** is the most concrete data point. Verified benchmarks around Hot Chips 2026 show it delivering **1.5x to 1.9x more work per watt** than Nvidia's Blackwell systems, with up to **3.6x lower end-to-end latency**. Crucially, it runs on OpenAI's own **Gluon kernel programming language**, deliberately bypassing CUDA for first-party workloads. This is a first-generation ASIC already competitive on efficiency, which validates the thesis that model developers can co-design hardware and software together.[[1]](https://www.nasdaq.com/articles/openais-jalapeno-chip-could-change-ai-hardware-race#1)[[3]](https://gadgetsnow.indiatimes.com/tech-news/openais-jalapeo-chip-posts-1-9x-nvidias-work-per-watt/amp_articleshow/133535847.cms#1)

**Anthropic** is assembling an in-house custom silicon team, with Broadcom reportedly handling design and Samsung Foundry on a 2nm node. It is pursuing a "multi-chip strategy," meaning it will still use Nvidia alongside its own designs—but the direction is clear.[[10]](https://www.design-reuse.com/news/202531258-samsung-foundry-to-manufacture-anthropic-ai-asic-on-2-nm-node/)[[11]](https://arstechnica.com:8080/ai/2026/08/anthropic-confirms-plans-to-build-an-in-house-silicon-team/#1)

The **hyperscaler ecosystem** provides the supply-chain depth you mention. Meta is scaling its Broadcom-designed **MTIA** accelerators on 2nm to reduce reliance on Nvidia and AMD. Amazon's custom chip business has crossed a **USD 20B annual run rate**, and Google's TPUs remain a proven alternative. Broadcom's AI semiconductor revenue grew **106% year-over-year** to USD 8.4B in Q1 FY2026, indicating the merchant custom-silicon model is maturing fast.[[38]](https://www.digitaltoday.co.kr/cn/view/48234/meta-to-roll-out-2-nm-mtia-ai-chip-at-scale-with-broadcom#none)[[40]](https://hashrateindex.com/blog/hyperscaler-ai-asic-market-report-part-1/#2)[[43]](https://www.linkedin.com/posts/paula-gutierrez-escacena_yesterday-meta-alphabet-microsoft-and-activity-7455602045337825280-IbyA#1)

### 🧠 AI-Generated Kernels: A Real but Partial Erosion

The "superhuman kernels" argument has moved from speculation to demonstrated capability. Research systems like **CUDA Agent** (ByteDance/Tsinghua) have achieved **92% faster rates than torch.compile** on complex kernels, and outperformed top proprietary models on the hardest benchmarks. Independent experiments claim to have rebuilt CUDA-like software in **10 hours** using AI coding agents.[[19]](https://www.c114.net.cn/industry/107379.html#1)[[48]](https://www.163.com/dy/article_v5/KN3EHALG0511AQHO.html?referFrom=#1)

However, this cuts both ways. The head of Nvidia's developer ecosystem notes that Nvidia itself is **using AI agents to accelerate CUDA development and verification**. More importantly, the hardest part of the moat may be **verification**, not initial code generation. As one founder argues, CUDA's deepest asset is its **validation toolchain**, which AI agents need to work efficiently—potentially *strengthening* the moat as AI coding scales. AI makes it easier to write a kernel; it does not automatically make it easy to prove that kernel is correct, performant, and safe across a production fleet.[[19]](https://www.c114.net.cn/industry/107379.html#1)

### ⚠️ Rubin's Ramp: A Timing Problem, Not a Moat-Killer

The Rubin delay is real but is being **over-attributed to Chinese suppliers**. TrendForce attributes the slower ramp to **HBM4 certification taking longer than expected**, networking upgrades, and power/cooling tuning. The claim that a single PCB supplier (Victory Giant) caused the delay has been publicly rebutted by the company and dismissed by industry analysts as lacking industrial logic. Rubin is now expected to ship in small volumes in **Q3 2026**, with meaningful ramp in Q4—still dependent on a broad, multi-national supply chain, but not uniquely hostage to China.[[29]](https://www.sohu.com/a/1040637354_120988576?scm=10001.325_13-325_13.0.0-0-0-0-0.5_1334&spm=smpc.channel_248.block3_308_NDdFbm_1_fd.1.1782232111448S5KjhEJ_324&_trans_=060008_lym#1)[[30]](https://money.udn.com/money/story/5603/9586712?from=edn_search_result)

### ⚖️ The Balance: Why the Moat Persists (For Now)

The erosion is real but **asymmetric**:

- **Inference vs. Training**: The custom-silicon and AI-kernel threats are strongest in **inference**, where workloads are narrower and efficiency matters most. Training frontier models at scale still overwhelmingly relies on Nvidia's mature, interconnected GPU clusters and the CUDA ecosystem's battle-tested distributed-training libraries.[[19]](https://www.c114.net.cn/industry/107379.html#1)
- **"Serious Labs" vs. Everyone Else**: OpenAI, Anthropic, Google, Meta, and Amazon can build bespoke stacks. The vast long tail of enterprises, startups, and research institutions cannot. For them, CUDA's **millions of lines of existing code, pretrained tooling, and hiring pool** remain a powerful lock-in.[[19]](https://www.c114.net.cn/industry/107379.html#1)
- **Nvidia's Counter-Move**: Nvidia is not static. Its argument is that as AI shifts to **inference and agentic workloads**, deep hardware-software co-design becomes *more* valuable, not less—and it is using AI to accelerate its own software stack.[[19]](https://www.c114.net.cn/industry/107379.html#1)

**The most defensible conclusion** is not that the CUDA moat will vanish, but that it will **narrow from an absolute monopoly to a dominant but contested standard**, primarily at the inference layer and among the largest, most technically capable customers. The "bespoke hobbyist experiments" framing understates the difficulty of replicating a full production stack, but it correctly identifies that the era of CUDA as the *only* serious option is ending.

---

## User

Demand for C++ experts will also be decimated with AI doing all the dev work?

---

## DeepSeek

The short answer is **no—not "decimated," but sharply bifurcated**. The evidence points to a market that is shrinking at the routine, application-level end while simultaneously *tightening* at the systems, performance-critical end. AI is not eliminating the need for C++ expertise; it is raising the bar for what counts as expertise and shifting the day-to-day work from writing code to supervising and verifying it.

### 📉 The Real Decline Is at the Application Layer

There is genuine data showing contraction. A Malt Tech Trends 2026 report found freelance demand for C++ projects fell **25%** over the past year, alongside similar declines for Java and PHP. This aligns with the broader observation that "basic coding skills alone" are losing value as AI handles more routine implementation. If your C++ work consists of writing standard business logic, gluing APIs together, or maintaining well-understood application code, that segment of the market is under real pressure.[[1]](https://workplacejournal.co.uk/2026/05/demand-for-traditional-coding-skills-falls-as-ai-tools-increase-in-popularity-malt/)[[3]](https://www.linkedin.com/posts/rohan009_softwareengineering-ai-programming-activity-7495872987464847362-0wsF)

### 🛡️ The Counter-Evidence: Systems Expertise Is Scarce, Not Surplus

The decline is not uniform. In domains where C++ is chosen not out of habit but because **performance, control, and hardware constraints actually matter**, demand remains robust or is even growing.

- **CUDA engineering is a direct counter-example.** Despite AI now generating and optimizing GPU kernels, U.S. job postings requiring CUDA skills in the first eight months of 2026 **already exceeded the total for all of 2025**. Nvidia alone had over 300 active U.S. openings, with base salaries advertised up to **USD 431,250**. The reason is that the deepest CUDA expertise was built over **20+ years**, and AI is currently filling a talent gap rather than eliminating the role.[[24]](https://africa.businessinsider.com/careers/ai-is-taking-over-the-painstaking-work-of-silicon-valleys-most-coveted-engineers/kl783s0#1)[[25]](https://www.webpronews.com/ai-agents-now-write-cuda-kernels-that-humans-struggle-to-explain/#1)
- **Low-latency and performance-critical systems remain C++ strongholds.** Recruiters report that "nothing has dethroned C++" for low-latency trading, exchange connectivity, and performance-critical infrastructure, with the bar for entry "just kept rising" rather than the market slowing. C++ remains described as irreplaceable in compilers, embedded systems, cybersecurity, game engines, and real-time systems.[[20]](https://www.linkedin.com/posts/abhinavcompilerllvm_c-project-ideas-domain-specific-compilersutra-activity-7309891560815439872-hGbO)[[32]](https://www.linkedin.com/posts/daniel-frugtniet-hagen-a4943719b_hiringtrends-activity-7425541983265488896-twha)
- **The structural driver is durable.** Herb Sutter's analysis argues that C++ and Rust have been the fastest-growing major languages because "software taketh away faster than hardware giveth"—demand for solving ever-larger computing problems consistently outpaces hardware capacity. AI is simply the latest source of demand to squeeze more performance out of hardware, not a force that removes the need for efficient languages.[[17]](https://herbsutter.com/tag/programming/#content)

### 🔄 The Nature of the Work Is Changing, Not Disappearing

The most important shift is qualitative. CUDA engineers increasingly spend their time **supervising AI coding agents**, setting high-level goals, evaluating outputs, and handling edge cases, rather than hand-writing every kernel. This has two consequences:[[24]](https://africa.businessinsider.com/careers/ai-is-taking-over-the-painstaking-work-of-silicon-valleys-most-coveted-engineers/kl783s0#1)[[25]](https://www.webpronews.com/ai-agents-now-write-cuda-kernels-that-humans-struggle-to-explain/#1)

1. **Junior-level work is most exposed.** AI lowers the barrier to entry for less experienced engineers, but it may hit junior CUDA engineers hardest, while specialists who can **outperform and verify AI's work** become more valuable.[[24]](https://africa.businessinsider.com/careers/ai-is-taking-over-the-painstaking-work-of-silicon-valleys-most-coveted-engineers/kl783s0#1)
2. **Verification becomes the premium skill.** AI can generate kernels that are faster than human-written ones but sometimes **defy full explanation**—the code works, but engineers cannot always explain every optimization decision. The scarce skill is no longer writing the code; it is **proving that the AI-generated code is correct, safe, and performant** in production systems.[[25]](https://www.webpronews.com/ai-agents-now-write-cuda-kernels-that-humans-struggle-to-explain/#1)

### 💎 Bottom Line

"C++ expert" is becoming a more **polarized** category. The broad middle of routine C++ application development is contracting under AI and low-code pressure. The narrow top—systems programmers who understand constraints, correctness, and hardware behavior—is facing **growing demand and rising compensation**, precisely because AI has made the easy parts easier and left the hard parts as hard as ever. The risk is not that C++ expertise becomes worthless; it is that the definition of "expert" moves upmarket, leaving those who stop at syntax-level proficiency behind.

---

## User

Would love to have C++ domain skills that would make me equally attractive to AI accelerator companies in China as to Nvidia. 🤔

---

## DeepSeek

The skill set that makes you equally attractive to Nvidia and to China's AI accelerator companies sits at the **intersection of deep C++ systems mastery and hardware-software co-design**—with one crucial twist. Nvidia wants you to push the boundaries of an already-mature ecosystem (CUDA). Chinese companies want you to **build the equivalent of CUDA from scratch** for their own silicon. Both value the same foundational depth, but the Chinese market demands greater **stack adaptability** across a fragmented hardware landscape.

### 🎯 The Universal Core: What Both Sides Fight For

These are the non-negotiable foundations. Every serious lab and chip company competes for engineers who have them.

- **Hardcore Modern C++ & Systems Programming**: This is not "C with classes." Both Nvidia and Chinese firms expect deep fluency in templates, multithreading, memory management, and low-level debugging. Nvidia's CUDA driver roles explicitly require "phenomenal C/C++ skills," experience with large codebases, and knowledge of OS interfaces for threads and virtual memory. Chinese job posts consistently list C++ proficiency alongside data structures and multithreading as a baseline.[[10]](https://aiot.csdn.net/69bd012e0a2f6a37c598edfd.html)
- **Computer Architecture & Heterogeneous Computing**: You must understand how the silicon actually moves data. This means **memory hierarchy, interconnects (NoC, PCIe), and parallelism at the hardware level**. Chinese listings for roles at Biren, Metax, and Cambricon explicitly ask for familiarity with heterogeneous computing and parallel programming (CUDA, ROCm, OpenCL). The broader AI Infra skill map emphasizes "understanding the hardware architecture (NPU/GPU storage, compute units)" as a core compiler skill.[[1]](https://www.career.zju.edu.cn/jyxt/sczp/zpztgl/ckZpgwXq.zf?zpxxbh=3CC44C9CBA2A506CE0653A68DD0E9B18)[[10]](https://aiot.csdn.net/69bd012e0a2f6a37c598edfd.html)
- **Performance Engineering as a Reflex**: The scarce skill is not writing a kernel that works; it is writing one that **saturates the hardware**. This means deep experience with **profiling (Nsight, vendor-specific tools), roofline analysis, and optimization for GEMM, Attention, and normalization operators**. The TechWire Asia analysis notes that Nvidia spent 400 engineer-months tuning a single model for its hardware, achieving 4x performance gains—illustrating that this optimization capability is the actual moat.[[38]](https://techwireasia.com/2026/10/nvidia-cuda-moat-ai-kernel-engineers-china/#content)

### ⚖️ The Divergence: Where the Two Markets Pull Apart

Your equal attractiveness comes from **straddling the stack**, not just going deep on one abstraction.

- **For Nvidia: Depth in the CUDA Abstraction**: Nvidia's frontier is extending CUDA itself—driver internals, new programming models (CUDA Graphs, MPS), and library design. They value engineers who can **evangelize and architect new CUDA features** and who have hands-on experience writing CUDA libraries. The moat is maintained by people who make the existing ecosystem faster and more expressive.
- **For China: Breadth Across a Fragmented Stack**: Chinese accelerator companies are building their software ecosystems (**CANN for Huawei, MXMACA for Metax**) under time pressure. They need engineers who can work **above and below the kernel layer**. This means competence in **compiler infrastructure (MLIR/LLVM, TVM)** to lower models to novel hardware, and **inference framework internals (vLLM, SGLang)** to optimize serving on chips that are still maturing. The goal is to reduce the "tuning bill" for customers switching away from Nvidia.[[5]](https://career.nankai.edu.cn/correcruit/content/id/118042.html)[[38]](https://techwireasia.com/2026/10/nvidia-cuda-moat-ai-kernel-engineers-china/#content)

### 💎 Your "Equal Attractiveness" Skill Recipe

To be a top candidate for both, build a **T-shaped profile**:

1. **Deep Vertical (Your C++ Core)**: Become formidable at low-level performance. Master **CUDA (and its concepts: warps, shared memory, occupancy)** not just as an API, but as a model for parallel thinking. Pair it with rigorous **systems debugging**—the ability to drop into GDB, understand assembly, and reason about cache coherence.
2. **Broad Horizontal (The Stack Bridge)**: Develop working competence in **MLIR/LLVM** and **Triton**. These are the lingua franca for both extending Nvidia's stack (e.g., new dialects) and building compilers for Chinese NPUs. A Chinese listing for a Cambricon compiler role explicitly lists **XLA/TVM and GCC/LLVM** as 加分项 (jiā fēn xiàng — bonus points). Understanding **PyTorch's internals (TorchScript, FX, dispatcher)** lets you see the full path from model graph to kernel.
3. **The Strategic Differentiator**: **Experience with a non-Nvidia software stack**—even academic or open-source. If you can demonstrate you have written a performant operator for a ROCm, OpenCL, or a simulated NPU backend, you prove you can generalize the CUDA mental model. This is precisely what Chinese companies need: engineers who can **translate CUDA patterns to new architectures** rather than just consume them.[[39]](https://workforcesignal.com/insights/developer-tools-ai-huawei-chips#main)

The market is bifurcating, but at the top, the skills converge on a single archetype: the **performance-minded systems engineer who understands the entire ML stack from graph to silicon**. Nvidia needs them to defend the frontier; Chinese companies need them to build a credible alternative. Mastering the C++ foundations and the compiler/kernel bridge makes you the same scarce asset to both.

---

## User

I’d want TileLang expertise in there too. What else?

---

## DeepSeek

Adding TileLang to your profile is a sharp move—it sits exactly where Nvidia and China's accelerator ecosystem are converging. The jobs that list TileLang don't stop there, though. They pair it with a specific constellation of complementary skills that turn a "kernel writer" into a **full-stack performance engineer**.

### 🧩 The Missing Pieces, Ranked by Leverage

**1. Compiler Infrastructure: The Bedrock Under TileLang**\
TileLang is built on **Apache TVM**, while its main rival Triton is built on **MLIR**. Understanding both ecosystems makes you valuable everywhere. The roadmap for AI hardware engineers explicitly lists **MLIR dialects, TVM, and LLVM** as the core of the compiler layer. A Shanghai AI-infra job posting for a custom NPU company names **Torch.compile, TileLang, TileScale, Triton, cuTile, MLIR, and TVM** as the compiler stack they want you to navigate. Your TileLang knowledge is strongest when you can trace a kernel from a Pythonic `T.prim_func` through TVM's lowering passes—and explain how that differs from Triton's direct MLIR path.[[3]](https://www.liepin.com/job/1984714501.shtml)[[10]](https://devpress.csdn.net/amd/6a10030210ee7a33f27460a6.html#1)

**2. Inference Runtime & Serving: Where Kernels Meet Production**\
Kernel-level skill is wasted if you can't integrate it into a serving stack. The same Chinese job posting lists **vLLM, SGLang, TensorRT-LLM, and TileRT** (a custom inference engine) as 加分项 (jiā fēn xiàng — bonus qualifications). This is the layer where TileLang kernels actually get deployed. Understanding **PyTorch's architecture and hardware adaptation interfaces** is also explicitly required. The ability to say "I wrote a TileLang kernel and dropped it into a vLLM pipeline on a non-Nvidia backend" closes the loop from research to product.[[3]](https://www.liepin.com/job/1984714501.shtml)

**3. Communication & Distributed Systems: The Hidden Multiplier**\
At cluster scale, a fast kernel is useless if the chip is starved for data. The Shanghai listing asks for **NCCL, NVSHMEM, or MPI** experience. The workforcesignal analysis of DeepSeek's Huawei move stresses that companies need engineers who can **tune communication libraries across distributed Ascend nodes** and understand **memory bandwidth limits and chip interconnects**. TileLang-Ascend work involves managing cluster synchronization and seeing "how memory tiles are scheduled" across nodes. This is the distributed-systems half of the performance equation.[[1]](https://workforcesignal.com/insights/developer-tools-ai-huawei-chips#main)[[3]](https://www.liepin.com/job/1984714501.shtml)

**4. Hardware Architecture & Co-Design: Speaking Silicon**\
Every serious accelerator role expects you to reason about the **memory hierarchy, NoC, and datapath** below the compiler. The 8-layer AI hardware roadmap puts **systolic arrays, HBM controllers, NoC, and UCIe** at the architecture layer. A founding accelerator-architect role at a YC startup asks for "a deep understanding of digital architecture, including datapaths, pipelining, and parallelism". You don't need to tape out silicon, but you *do* need to know why a TileLang scheduling decision maps poorly to a particular SRAM bank conflict or interconnect topology.[[27]](https://www.ycombinator.com/companies/lamb-labs/jobs/QfZbNOf-founding-ai-accelerator-architect-research-hardware-co-design)

**5. Low-Level Runtime & Driver: The C++ Bedrock Persists**\
The systems-programming foundation from our last exchange doesn't disappear—it gets more specific. The hardware roadmap's runtime layer lists **C++ runtime, Linux kernel drivers (PCIe/DMA), and CUDA-like API design**. A Khosla Ventures job board listing for accelerator systems roles demands **C/C++/Rust**, experience with **runtimes, drivers, firmware, concurrency, synchronization, and memory-ordering semantics**. Your C++ depth is what lets you debug the layer *beneath* TileLang when the generated kernel behaves unexpectedly on new hardware.[[26]](https://jobs.khoslaventures.com/companies/openai/jobs/91050574-software-engineer-ai-accelerator-runtime#content)

### 🎯 The Unified Profile

The people who move fluidly between Nvidia and Chinese accelerator companies are not just "TileLang experts." They are engineers who can **own the vertical slice** from a PyTorch graph down to a TileLang kernel, then across a distributed communication fabric, and debug the whole path when performance regresses. TileLang is the visible DSL; the invisible scaffolding is **TVM/MLIR literacy + serving-stack fluency + distributed-systems awareness + architectural intuition + C++ runtime depth**. The workforcesignal analysis is blunt about the payoff: "Those low-level skills command a high premium because few developers looked beyond CUDA". Your advantage compounds with each layer you add around TileLang.[[1]](https://workforcesignal.com/insights/developer-tools-ai-huawei-chips#main)

---

## User

I’m guessing that if all I have on hand is my trusty M5 MBP, I could still sharpen my chops on a significant portion of all that we’ve discussed. Say I download a 1B or some other toy model and try to optimize it for my MBP’s NPU?

---

## DeepSeek

Yes, your M5 MacBook Pro is actually a surprisingly capable training ground for a significant slice of what we discussed—with one important caveat: **you can practice the kernel/compiler layer on the GPU (Metal), but optimizing for the NPU (ANE) specifically is a much more constrained and Apple-specific path.**

### ✅ What You *Can* Sharpen on the M5

**TileLang Itself Works on Apple Silicon.** TileLang has a supported **Apple Metal backend** for macOS on Apple silicon, with release wheels and CI coverage. Notably, the docs mention **Metal 4 cooperative tensors are available on supported M5 systems**, which is directly relevant to your hardware . This means you can install TileLang, write kernels targeting `metal`, and profile them on your M5's GPU. That alone lets you practice the DSL, the scheduling abstractions, and the mental model of tiling for a non-CUDA architecture.[[5]](https://tilelang.com/_sources/get_started/targets.md.txt)

**The TVM/Metal Compiler Path Is Real (and Buggy).** Since TileLang is built on TVM, working with the Metal target gives you exposure to TVM's lowering pipeline and code generation. There's even an open TVM issue documenting a Metal codegen bug that produces silently wrong output on a HiFi-GAN-style graph, with a reproducible ONNX model and a clean Python repro script . This is a *gift* for learning: you can reproduce a real compiler correctness bug, compare LLVM vs Metal outputs, and potentially dig into the lowering passes that cause the divergence. That's exactly the kind of debugging skill that matters in accelerator compiler work.[[4]](https://github.com/apache/tvm/issues/20157#1)

**1B Models Run Fine, and You Can Convert Them.** A 1B model is trivial for an M5 MBP. You can:

- Run it via **PyTorch MPS** by moving tensors to `device="mps"`.[[2]](https://docs.pytorch.org/docs/2.15/notes/mps.html)
- Convert it to **MLX** for high-throughput inference in Python .[[11]](https://raw.githubusercontent.com/OpenBMB/MiniCPM/main/docs/deployment/mlx.md#1)
- Convert it to **Core ML** and experiment with compute unit placement (CPU/GPU/ANE) using `coremltools`, checking which ops land on the ANE via Xcode's performance report .[[3]](https://huggingface.co/apple/coreml-mobileclip/discussions/1#1)[[8]](https://tech.ailia.ai/en/using-mixed-precision-in-core-ml-77c2428ba728/)

### ⚠️ The NPU (ANE) Caveat: It's Not a General-Purpose Target

The ANE is **not** like a CUDA GPU or even the M5's GPU. You cannot simply point TileLang or a custom kernel at it. The path to the ANE is **Core ML**, and the compiler decides op placement based on how the computation is *expressed*, not what it computes.

Research on LLM placement on the ANE found that **a fused RMSNorm is fully ANE-eligible while its arithmetically identical decomposition is CPU-only** . Weight encoding also gates the accelerator: an fp16 conv-heavy model was assigned entirely to the CPU, while the same graph in int8 or 2-bit returned to ~83% residency and ran **1.8–2.2× faster** . This means your "optimization" work on the ANE is really **graph-level Core ML engineering**: quantization choices, op fusion patterns, and inspecting the compute unit mapping—not writing low-level kernels.

### 🎯 A Concrete "Chops-Sharpening" Project for Your M5

1. **Download a 1B model** (e.g., MiniCPM5-1B or Qwen3-0.6B). Both have known conversion pipelines for Apple hardware .[[1]](https://huggingface.co/mlboydaisuke/MiniCPM5-1B-CoreAI/blob/5ad650fdb0ce51207c7bd9ed4585c6154a7c1fb8/README.md#1)[[9]](https://github.com/anemll/anemll/blob/f4ad26d061dc2e426faa19f81c367343bdeb9f0d/README.md)
2. **Baseline it in PyTorch MPS**: measure tokens/sec, memory, and where time goes.
3. **Convert to Core ML** with `coremltools`, setting `ComputeUnit.ALL`. Use Xcode's performance report to see the op-to-device split . Identify which ops fall to CPU.[[3]](https://huggingface.co/apple/coreml-mobileclip/discussions/1#1)
4. **Quantize to int8 or 4-bit** and re-measure. Watch how the ANE residency changes—this teaches you the encoding-first design principle the research highlights .
5. **Separately, write a TileLang kernel** for a simple op (GEMM or a fused norm) targeting `metal`. Profile it. Compare its performance to the PyTorch MPS equivalent. If you're ambitious, try to trigger the TVM Metal codegen bug from the GitHub issue and trace it .[[4]](https://github.com/apache/tvm/issues/20157#1)

This gives you hands-on experience with the **full stack** on one machine: model → runtime → compiler → kernel → hardware, with the ANE forcing you to think about graph-level constraints that are very different from GPU kernel optimization. What you *won't* get is practice with the CUDA-specific tooling (Nsight, CUDA Graphs) or the fragmented NPU software stacks (CANN, MXMACA) that Chinese accelerators use—those require the actual hardware or cloud access. But the underlying skills of reasoning about memory hierarchy, operator fusion, quantization trade-offs, and compiler correctness are all exercisable on your M5.

---

## User

I’m not interested in CUDA mastery except for areas which can be leveraged into skilling up for the myriad accelerators that are certainly coming down the pike.

---

## DeepSeek

If CUDA mastery is off the table except where it serves as a **transferable abstraction**, your target isn't CUDA syntax—it's the **portable layer** and the **semantic bridge** that lets one mental model travel across GPUs, NPUs, and whatever else arrives.

The most valuable CUDA-adjacent knowledge for a multi-accelerator future is the stuff that **explicitly exists to escape CUDA**, or that **translates CUDA's semantics** into something a non-Nvidia chip can execute.

### 🧠 Learn CUDA's *Model*, Not Its API

The durable asset is understanding the **SIMT execution model, the memory hierarchy (shared memory, global memory, synchronization), and the warp/block/grid abstraction**. These are the concepts that portable layers must preserve or translate.

**HIP** is the most direct example. It's a C++ runtime API and kernel language that lets you write portable code running on both AMD and NVIDIA GPUs from a single source . HIP is deliberately thin—it has little or no performance impact over coding directly in CUDA mode . Learning HIP is effectively learning CUDA's programming model while training yourself to think in a vendor-neutral way. The `hipify` tools convert CUDA to HIP, but the real skill is understanding what maps cleanly and what requires manual tuning .[[7]](https://packages.debian.org/zh-cn/sid/hipcc?pow_referer=)

**SYCL** goes further into standard C++. DPC++ (Intel's SYCL implementation) is an LLVM fork that compiles kernel code for multiple platforms, bundling device code within the final binary . Benchmarks show SYCL achieving performance equivalent to optimized CUDA on the same hardware, with the programmer choosing how much to specialize hot loops versus how much to abstract . This teaches you the **performance-portability tradeoff** as a design skill, not a slogan.[[15]](https://zenodo.org/records/7657431/files/WAMTA23%20Hugh.pdf?download=1#1#1#1)

### 🔄 The CUDA-to-NPU Translation Layer: The Real Frontier

This is where your TileLang/compiler interest meets the accelerator fragmentation you're anticipating. Chinese NPUs (Ascend, Cambricon, etc.) don't have warp schedulers; they use **coarse-grained 2D tensor instructions**. The semantic gap is fundamental: CUDA relies on implicit scalar thread parallelism, while NPUs need explicit 2D tiling.[[2]](https://sklp.ict.ac.cn/yjcg/202602/t20260211_823822.html)

A CGO 2026 Distinguished Paper award went to **T2T**, a compiler that translates CUDA kernels to NPU code via **2D vectorization**. The key insight: it captures CUDA's "all threads execute in parallel" semantics in a **Unified Parallel Abstraction (UPA)**, then systematically converts the thread hierarchy into explicit nested loops that a compiler can vectorize into NPU 2D instructions . The translated kernels reached up to **73% of A100 GPU native hardware utilization** on an NPU, with a **6.9× speedup** over traditional 1D vectorization .[[2]](https://sklp.ict.ac.cn/yjcg/202602/t20260211_823822.html)

This is exactly the kind of work that makes CUDA knowledge **transferable rather than tribal**. Understanding how CUDA semantics get *rewritten* for a different execution model is more valuable than being able to hand-optimize a CUDA kernel for an H100.

### 🧩 Practical Portable Targets to Build On

**ZML/v2** is a concrete example of a single-codebase inference stack that lowers models directly onto **NVIDIA, AMD, TPU, and Trainium targets** without the Python-heavy runtime layers . Its API centers on an explicit `Platform` abstraction; you can build for CUDA, ROCm, TPU, or Neuron via compile-time flags . Studying how it expresses **sharding, attention backends, and memory allocation** across these targets teaches you what a genuinely accelerator-agnostic stack looks like.[[1]](https://zml.ai/posts/zml-v2/)

**Triton** is another practical entry point. It lets you write high-level Python code that compiles to optimized kernels on AMD GPUs, reducing dependence on proprietary implementations . The mental model—block-level programming, compiler-managed scheduling—is closer to TileLang than to hand-written CUDA, and it's already supported by multiple vendors.[[4]](https://www.amd.com/content/dam/amd/en/documents/instinct-tech-docs/white-papers/ai-portability-by-design.pdf#1#1#1)

### 🎯 The Skill Recipe for "Myriad Accelerators"

1. **Learn SIMT semantics through HIP**, not CUDA. You get the same mental model (warps, shared memory, barriers) but in a portable C++ dialect. Read the HIP docs alongside CUDA docs to see where they diverge.
2. **Study T2T's UPA abstraction and 2D vectorization**. This is the clearest published example of how CUDA semantics get **systematically decomposed** for a different hardware model. Understand why 1D vectorization fails and 2D tiling succeeds .[[2]](https://sklp.ict.ac.cn/yjcg/202602/t20260211_823822.html)
3. **Build something in ZML or a similar portable stack**. Pay attention to the `Platform` abstraction, explicit sharding, and pluggable attention backends . The goal is to internalize what a **hardware-agnostic programming model** requires.[[1]](https://zml.ai/posts/zml-v2/)
4. **Use TileLang as your kernel DSL** (as you planned). Its TVM foundation and multi-backend trajectory make it a natural bridge between high-level model code and low-level accelerator code.
5. **Keep your C++ depth for the runtime/compiler layer**, not the CUDA API surface. The portable layers still need engineers who can debug memory ordering and synchronization beneath the abstraction.

The CUDA knowledge that matters for the coming accelerator plurality is the knowledge that lets you **decompose CUDA's assumptions** and **rebuild them elsewhere**—not the knowledge that lets you squeeze the last 5% out of an Nvidia GPU. The moat you want to cross is the **semantic gap**, and the bridge is built from portable abstractions, translation compilers, and explicit execution-model reasoning.

---

## User

We could potentially treat the M5 NPU as an “unknown newcomer” we were asked to optimize against? Or does Apple firewall their NPUs off?

---

## DeepSeek

You can absolutely treat the M5's NPU as an "unknown newcomer" to optimize against—but the catch is that **Apple's official firewall is very real, and getting past it to do the kind of low-level work you want requires deliberately stepping outside Apple's supported developer path.**

### 🚧 The Official Firewall: Core ML as a Black Box Scheduler

Through public, supported APIs, the ANE is not a programmable accelerator in the way a GPU or an NPU from Qualcomm/Huawei is. It is a **fixed-function block reachable only through Core ML**, which treats the ANE as one scheduling option among CPU and GPU . You do not write kernels for it; you express a model in a supported format and hope the compiler assigns ops to the ANE.[[2]](https://huggingface.co/mattmireles/kokoro-coreml/blob/26ef451bccb125fce8dfc87878a9b3091535e136/README/coreml-conversion-guide.md#1)

The constraints are severe and instructive for someone learning to optimize against unfamiliar hardware:

- **Precision and layout are rigid**: FP16 weights and specific 4-D tensor layouts are required, or the model silently falls back to CPU/GPU .[[2]](https://huggingface.co/mattmireles/kokoro-coreml/blob/26ef451bccb125fce8dfc87878a9b3091535e136/README/coreml-conversion-guide.md#1)
- **One bad op poisons the whole graph**: A single unsupported operation typically forces the rest of the model onto the fallback device .[[2]](https://huggingface.co/mattmireles/kokoro-coreml/blob/26ef451bccb125fce8dfc87878a9b3091535e136/README/coreml-conversion-guide.md#1)
- **The ISA is undocumented**: Apple does not publish the ANE instruction set, so official development is purely at the graph level .[[2]](https://huggingface.co/mattmireles/kokoro-coreml/blob/26ef451bccb125fce8dfc87878a9b3091535e136/README/coreml-conversion-guide.md#1)

This is actually a useful forcing function. It teaches you to reason about **operator eligibility, fusion patterns, and layout constraints** before you ever touch a kernel—exactly the kind of thinking that transfers to any opaque NPU.

### 🔓 The "Unknown Newcomer" Path: Private APIs and Research Tooling

If you want to treat the ANE as a genuine target for optimization experiments, the research community has already built the bridges—but they are explicitly **unentitled, private-API-based, and not production-supported**.

**ANEForge** is the most relevant tool for your purposes. It is a Python package that compiles a lazy tensor graph directly to a single ANE program, bypassing Core ML entirely. It dispatches through the same `aned` daemon and kernel driver that Apple's own frameworks use, but from an ordinary user process with **no Apple entitlement**. It supports 58 fused operators and 19 native bridge operators, runs on M5 hardware (benchmarks are reported on an M5 Pro), and can even train on the engine .[[4]](https://onlinelibrary.wiley.com/doi/10.1002/spe.70124#1)[[8]](https://pypi.org/project/aneforge/0.3.0/#1)

For your "unknown newcomer" exercise, this is powerful because it gives you **direct access to the hardware's actual constraints** without Core ML's scheduler deciding for you. You can measure:

- **Dispatch floor**: A small fused program completes in about 90µs, near the engine's ~70µs per-program dispatch floor .
- **Workload fit**: ResNet-18 runs in 0.33ms with 2.2 mJ energy, while ViT-B/16 takes 18.3ms and 75 mJ—showing exactly where the ANE excels and where it doesn't .[[8]](https://pypi.org/project/aneforge/0.3.0/#1)
- **Training feasibility**: Orion (another research system) demonstrated stable training of a 110M-parameter transformer on the ANE for 1,000 steps, with a trick to reduce weight-update recompilation from 4.2s to 494ms per step .

### ⚠️ The Critical Caveats

**This is not a supported development path.** ANEForge and Orion rely on private frameworks (`AppleNeuralEngine.framework`, `_ANEClient`, `_ANECompiler`) that Apple can change or lock down at any macOS update . The tools are research artifacts, not stable platforms.

**The ANE's "generality" is limited.** Even with direct access, the engine has no data-dependent control flow, bakes weights at compile time, and has a hard dispatch floor that makes small operations inefficient . Treating it as an "unknown newcomer" will teach you its quirks, but those quirks are not a proxy for, say, a Huawei Ascend or a Groq chip.[[4]](https://onlinelibrary.wiley.com/doi/10.1002/spe.70124#1)

### 🎯 What This Exercise Actually Buys You

If your goal is to **sharpen transferable accelerator-optimization instincts**, the M5 ANE is a legitimate training ground—provided you go in with the right expectations:

1. **You will learn to read a black-box hardware profile** from measured latency, energy, and operator-eligibility data, not from a vendor programming guide. That skill transfers directly to any new accelerator with thin documentation.
2. **You will internalize the cost of dispatch and compilation**. The ANE's ~70µs dispatch floor and weight-baking behavior force you to think about **granularity and state residency** in a way that GPU work often doesn't .
3. **You will practice the Core ML "op surgery" mindset**—rewriting a model so that its operations fall within the hardware's supported set. This is exactly what engineers do when porting models to new NPUs .[[2]](https://huggingface.co/mattmireles/kokoro-coreml/blob/26ef451bccb125fce8dfc87878a9b3091535e136/README/coreml-conversion-guide.md#1)

What you **won't** get is experience with a programmable SIMT/vector ISA, shared-memory hierarchies, or the kind of kernel-level tuning that TileLang and Triton target. The ANE is too opaque and too constrained for that. Use it as a **graph-level and systems-level optimization exercise**, and keep the GPU path (via TileLang's Metal backend) for the kernel-level work. Together, they cover both halves of the multi-accelerator skill set you're building.

---

## User

That’s a valid approach with respect to the ANE — I appreciate the insight. I’ll cross that bridge when I come to it, I guess, as new Chinese accelerators are meant for domestic eyes only.

---

## DeepSeek

That's a fair read, and it's worth being clear-eyed about it: the Chinese accelerator ecosystem is **structurally hard to access from outside**, but "domestic eyes only" overstates the closure. The barriers are real but uneven, and some of them are softening.

### 🔒 What's Genuinely Closed

**The high-end silicon is export-controlled and domestically prioritized.** Huawei's Ascend roadmap (950PR/950DT, 960, 970) is aimed at domestic hyperscalers, and the company has signaled it may **keep its best chips for China** while exporting lesser versions. Cambricon and others operate under the same policy gravity—domestic allocation first. You won't be buying a card or getting cloud access to a 950PR from abroad anytime soon.

**The software stacks are Chinese-first.** CANN documentation, community forums, and much of the tooling are primarily in Chinese. That's a real friction, though not an absolute wall—machine translation handles most documentation, and the code (C++, Python, MLIR) is language-neutral.

### 🔓 What's Actually Accessible

**Open-source software is not firewalled.** This is the important part for your skill-building. Chinese labs are publishing aggressively:

- **TileLang itself** is open-source, has a **TileLang-Ascend** backend, and is developed with Chinese academic and industrial participation. You can read, build, and contribute to it today.
- **vLLM-Ascend**, **MindSpore**, and pieces of the **CANN** toolchain have open components on Gitee and GitHub.
- **DeepSeek's** technical reports and kernel-level work (e.g., their FP8 training and communication-overlap techniques) are public and describe hardware-software co-design in detail.

**Cloud access exists, with caveats.** Some Chinese cloud providers offer Ascend-based instances, though access from abroad is inconsistent and often requires a Chinese account. It's not reliable enough to build a workflow around, but it's not zero.

**The talent flow is two-way.** Chinese accelerator companies recruit internationally, and engineers with portable-stack experience move between ecosystems. The skills you're building—TileLang, TVM/MLIR, distributed-systems reasoning—are **legible to both sides** precisely because they're not tied to one vendor's API.

### 🎯 The Practical Implication for Your Plan

Your instinct to build **portable, hardware-agnostic skills** is the right hedge against this asymmetry. You don't need physical access to an Ascend chip to:

1. **Read and contribute to TileLang-Ascend**—the backend code and tests are open, and understanding how it maps TileLang's abstractions onto Ascend's execution model is exactly the "translation layer" skill we discussed.
2. **Study published kernel work** from DeepSeek, Alibaba (PAI), and others—their technical reports describe the optimization reasoning, not just the results.
3. **Build on the portable layers** (TVM, MLIR, Triton, ZML) that both ecosystems converge on.

The "domestic eyes only" framing is accurate for **silicon access**, less so for **software and knowledge**. The bridge you're building—portable abstractions, compiler infrastructure, explicit execution-model reasoning—is the part that travels regardless of which side of the firewall the hardware sits on. When access does open up, or when a non-Chinese accelerator with similar constraints arrives, you'll be positioned to move quickly.

---

## User

Any affordable AI accelerator that I can get raw access to for practice? Or are there emulators for such chips? Or perhaps like you’ve alluded to such skills don’t really move the needle as if I were able to master all that we’ve discussed, having experience optimizing for a totally new chip wouldn’t enhance one’s resume in meaningful ways?

---

## DeepSeek

Yes, there are affordable options for raw access, and simulators. More importantly, your concern that this experience "wouldn't move the needle" is **wrong**—the hiring signal for accelerator work in 2026 is shifting precisely toward people who can demonstrate porting and optimization on *non-Nvidia* hardware, even at a small scale.

### 💰 Affordable Hardware with Raw Access

You don't need a datacenter chip to practice the skills we've discussed. Several options exist at hobbyist/prosumer prices:

**Tenstorrent Blackhole (USD 999–1,399)** is the strongest choice for your goals. It's a PCIe card built on RISC-V cores with a fully **open-source software stack** (TT-Metalium, TT-NN under Apache 2.0). Critically, the software is still under active development, which means there are real optimization problems to solve—exactly the kind of "unknown newcomer" experience you want. You get 120 Tensix cores, 28–32 GB GDDR6, and a programming model far from CUDA .[[9]](https://www.aquanode.io/blog/tenstorrent-vs-nvidia)

**DFRobot DX-M1 (USD 139)** is a cheap M.2 inference accelerator (25 TOPS, 4 GB RAM). It's strictly for edge inference (YOLO, MobileNet), not LLMs, but it gives you a taste of compiling models through a vendor SDK (DXNN) for unfamiliar silicon .[[1]](https://wccftech.com/dfrobot-dx-m1-25-tops-m2-ai-accelerator-module-raspberry-pi-pc/#comments)

**Banana Pi BPI-SM10** (RISC-V, 60 TOPS, supports 30B models locally) is another edge option, though pricing and availability are less clear from search results .[[10]](https://www.jonpeddie.com/news/banana-pi-gives-risc-v-an-edge-ai-board-for-large-local-llms/#content)

### 🖥️ Simulators and Cloud Alternatives

**Wolfpine** is a pure-Python simulator for Tenstorrent's tt-metal stack. It lets you run tt-metal programs against simulated Wormhole or Blackhole hardware with **no code changes**—the same program you'd run on real silicon runs against the simulator via environment variables . This is perfect for learning the programming model before buying hardware, or if the USD 999 card is out of budget.[[2]](https://pypi.org/project/wolfpine/2.2/#files#1)

**Google's Coral NPU simulators** offer both a fast behavioral simulator (MPACT-CoralNPU) and a cycle-accurate Verilator simulator, with open-source files and a Python harness for ML kernel correctness testing .[[11]](https://developers.google.cn/coral/guides/software/simulator#using_the_mpact-coralnpu_behavioral_simulator#1)

**AMD's AI Developer Program** gives free cloud credits (equivalent to ~50 GPU hours) and access to ROCm, no AMD hardware required .[[8]](https://baike.baidu.com/item/AMD%20AI%20%E5%BC%80%E5%8F%91%E8%80%85%E8%AE%A1%E5%88%92/67454977?bst=1792057122.e2c7e4017355fc87)

### 🎯 Why This Actually Moves the Resume Needle

The argument that "optimizing for a new chip doesn't enhance a resume" is contradicted by how the market is evolving. The hiring signal in 2026 is moving toward **portability and migration experience**, not vendor-specific depth.

A skills block that opens with **PyTorch, Triton, XLA, Neuron SDK** rather than CUDA-first signals breadth to a TPU shop or an accelerator startup. The most compelling resume bullet is now a **migration story**: "Ported a workload off GPUs onto X, held correctness, improved cost per step by Y%." Accelerator companies themselves are hiring for this—an early-stage chip startup's ML architect role explicitly asks for deep model-training experience and excitement about applying it to novel hardware, with **"no prior hardware experience required"** .[[4]](https://www.hrlens.io/articles/ml-engineer-resume-cuda-2026)

The caveat is that a USD 139 edge chip or a simulator won't teach you datacenter-scale distributed training. But it *will* teach you the core skill that transfers: reading an unfamiliar hardware profile, understanding its constraints (memory hierarchy, dispatch overhead, operator eligibility), and proving you can make a real workload run better on it. That is the "unknown newcomer" exercise, and it's directly legible to hiring managers building the next generation of accelerators.

If you want the highest-leverage single purchase, the **Tenstorrent Blackhole** paired with **Wolfpine for practice** is the closest thing to a genuine "new accelerator" playground that fits a reasonable budget and aligns with the open-stack philosophy you've been building around.

---

## User

What are the official names or titles for folks with these skills? The ones doing the actual work, not project managers or tech leads

---

## DeepSeek

The people doing the actual hands-on work fall into a few distinct titles, and the naming splits cleanly along the **kernel-level** versus **compiler-level** divide. For the portable, multi-accelerator skill set you've been building, you'll want to watch for both categories, plus a third "porting" role that sits between them.

### 🛠️ The Kernel-Level Titles (Closest to the Metal)

These are the roles writing and hand-optimizing the code that runs on the silicon.

- **GPU Kernel Engineer / Member of Technical Staff, GPU Kernels**: This is the most direct match for low-level optimization. SF Tensor, for example, uses this title for engineers who hand-write kernels across NVIDIA, AMD, TPU, and Trainium, debug down to the ISA level, and work below PTX . The focus is on beating vendor libraries and understanding microarchitectural behavior.[[4]](https://speedrun-talent-network.com/jobs/member-of-technical-staff-gpu-kernels-sf-tensor-2238bd4b)
- **Senior GPU Kernel Performance Engineer**: Nvidia uses this title for engineers designing and optimizing kernels for inference, with explicit requirements for CUDA C/C++, cuTile, or Triton experience .
- **Senior GPU Kernel Optimization Engineer**: AMD's version of the role, requiring CUDA, HIP, or Triton, and focusing on profiling, kernel fusion, and architecture-aware tuning .[[9]](https://careers.amd.com/careers-home/jobs/92727#1)
- **算子开发工程师 (suànzǐ kāifā gōngchéngshī — Operator Development Engineer)**: This is the standard Chinese title for kernel-level work. Companies like 沐曦 (Mùxī — MetaX) list it under their software roles, with responsibilities for operator development, functional testing, and performance tuning . 墨芯 (Mòxīn — MoffettAI) lists it explicitly for campus recruitment .[[3]](https://career.sysu.edu.cn/attachment/sysu/ueditor/file/20260902/4676_%e6%b2%90%e6%9b%a6%e8%82%a1%e4%bb%bd27%e6%a0%a1%e6%8b%9b%e6%8b%9b%e8%81%98%e7%ae%80%e7%ab%a0.pdf#1#1#1)[[8]](https://moffettai.com/jia-ru-wo-men/)

### 🧠 The Compiler-Level Titles (The TileLang/TVM/MLIR Layer)

These roles build the toolchains that generate or optimize kernels, which aligns directly with your TileLang and TVM interests.

- **Machine Learning Compiler Engineer**: Qualcomm's Compiler Labs uses this exact title, listing MLIR, MLIR Dialects, TVM, Triton, and LLVM as required experience .[[2]](https://jobs.abven.com/companies/nuvia/jobs/63366576-machine-learning-compiler-engineer#content)
- **AI编译工程师 (AI biānyì gōngchéngshī — AI Compilation Engineer)**: A very common title in Chinese chip companies. The variants are specific: **算子开发和优化工程师** (suànzǐ kāifā hé yōuhuà gōngchéngshī — Operator Development and Optimization Engineer) and **图编译器开发工程师** (tú biānyìqì kāifā gōngchéngshī — Graph Compiler Development Engineer) both appear in job postings . 墨芯 (Mòxīn — MoffettAI) lists **大模型AI编译器工程师** (dà móxíng AI biānyìqì kāifā gōngchéngshī — Large Model AI Compiler Engineer) as a distinct role .[[5]](https://jy.scu.edu.cn/index/index/employjobdetail.html?data=MDAwMDAwMDAwMJG6n3_Ed6imi4qQtLh4Y92Kzrayspzddricp9CWi5qikaeWacSdqLqGfaK2w4iil5C4zNbGiL-E)[[8]](https://moffettai.com/jia-ru-wo-men/)
- **AI编译优化高级研究员 (AI biānyì yōuhuà gāojí yánjiūyuán — Senior Researcher, AI Compilation Optimization)**: Lenovo's title for a more senior compiler role, requiring deep TVM/MLIR/Triton expertise and heterogeneous chip architecture knowledge .[[10]](https://jobs.lenovo.com/zh_CN/careers/JobDetail/AI/57480)

### 🔄 The "Porting" Title (The Multi-Accelerator Bridge)

This is the role that most directly matches your "unknown newcomer" exercise, and it exists at hardware companies trying to make their silicon usable.

- **Machine Learning Engineer, AI Models (Tenstorrent)**: Tenstorrent's description is essentially your practice project as a job. The role owns "porting, tuning, and validating LLMs and vision models on our accelerator," traces bottlenecks from PyTorch down to kernels and memory systems, and works with compiler/kernel/hardware teams. Notably, deep CUDA experience is a **bonus, not required**—the core is model expertise plus the ability to bring workloads onto new hardware .[[6]](https://aidevboard.com/job/machine-learning-engineer-ai-models-ed6538f8)[[12]](https://careers.georgian.io/companies/tenstorrent/jobs/59507371-machine-learning-engineer-ai-models#content)

### 🎯 The Pattern for Your Resume

If you want your resume to read as a multi-accelerator candidate rather than a CUDA specialist, the titles to target are **GPU Kernel Engineer** (for the low-level proof) and **ML Compiler Engineer** (for the TileLang/MLIR bridge), with **Machine Learning Engineer, AI Models** as the entry point that explicitly values porting experience over vendor lock-in. The Chinese market uses **算子开发工程师** (suànzǐ kāifā gōngchéngshī — Operator Development Engineer) and **AI编译工程师** (AI biānyì gōngchéngshī — AI Compilation Engineer) as the direct equivalents, and both appear in the same company's hiring list—meaning the stack you're building spans both titles.

---

## User

TileLang-level experts don’t seem to need to go as bare metal as the kernel engineers?

---

## DeepSeek

Your observation is largely correct, but with an important nuance: **TileLang experts don't need to manually handle the same level of bare-metal details as traditional kernel engineers (such as manually managing shared memory, synchronization, and register allocation), but they still need to understand the underlying hardware behavior well enough to "direct" the compiler where performance matters.**

### The Abstraction Layer TileLang Handles for You

The core design goal of TileLang is precisely to liberate developers from the tedious hardware details of handwritten CUDA. When writing traditional CUDA kernels, engineers must manually handle shared memory declaration and padding, thread synchronization, register allocation to avoid spills, instruction selection (WMMA/MMA), and software pipelining . TileLang encapsulates these low-level concerns as compiler responsibilities: developers use Python DSL to describe **what to compute** (data tiling, computation logic), and the compiler handles **how to compute** (memory allocation, instruction scheduling, pipeline optimization) .[[3]](https://raw.githubusercontent.com/ForceInjection/AI-fundamentals/refs/heads/main/02_gpu_programming/03_tilelang/01_tilelang_quick_start.md#1)

This means that a TileLang expert writing a GEMM or FlashAttention kernel does not need to manually write `__syncthreads()` or calculate bank conflict padding. TileLang's layout inference and pipeline inference will automatically complete these tasks . From this perspective, the depth of bare-metal intervention is indeed much shallower than that of traditional kernel engineers.[[12]](https://raw.githubusercontent.com/zhaoyang97/Paper-Notes-en/refs/heads/main/docs/ICLR2026/llm_efficiency/tilelang_bridge_programmability_and_performance_in_modern_neural_kernels.md#1)

### But This Does Not Mean You Can Completely Ignore Hardware

The key distinction lies in: TileLang experts need to know **when to manually intervene** and **how to intervene**. TileLang's design philosophy is "separation of dataflow and scheduling"—automatic inference handles most decisions, but performance-sensitive parts allow developers to override .[[10]](https://github.com/ai-hpc/ai-hardware-engineer-roadmap/blob/35de1073c4b45ace898f3bdb6a5f6efe20239e2f/Phase%205%20-%20Advanced%20Topics%20and%20Specialization/7.%20ML%20Systems%20Engineering/MLSys%20Deep%20Dives/Lecture-02.md#1)[[13]](https://raw.githubusercontent.com/ai-hpc/ai-hardware-engineer-roadmap/refs/heads/main/Phase%205%20-%20Advanced%20Topics%20and%20Specialization/Track%20G%20-%20ML%20Systems%20Engineering/MLSys%20Deep%20Dives/Lecture-02.md#1)

Practical evidence: In an official TileLang tutorial, the compiler's automatically generated code exhibited counterintuitive behavior when processing vectorized additions (although vectorization caused each thread to process 8 elements, the kernel launch still retained 256 threads, resulting in only 32 threads actually active). Developers needed to explicitly specify the number of elements processed per thread to "guide" the compiler to generate code that better matched the intent . This requires the ability to read the generated CUDA code and judge whether its behavior is reasonable.[[8]](https://github.com/tile-ai/tilelang/blob/752312c2a92ed9318789391ff69454b160bd4904/docs/deeplearning_operators/elementwise.md)

Another example: When optimizing FlashAttention on AMD MI300X, engineers needed to select the optimal combination from 108 configurations (block_M=128, block_N=32, threads=512, etc.), a process that relied on understanding hardware characteristics such as SRAM utilization and parallel efficiency . TileLang's autotuning can accelerate the search, but knowing which parameters are worth searching and how large the search space should be still requires hardware intuition.[[6]](https://rocm.blogs.amd.com/ecosystems-and-partners/rocm-tilelang-kernel/README.html)

### The Actual Skill Profile of TileLang Experts

From actual job postings, "deep experience writing CUDA kernels or equivalent (CuTeDSL, Triton, TileLang, Pallas)" is a hard requirement . This indicates that employers view TileLang as an **alternative expression** of kernel capabilities, not as a lower-level skill. A qualified TileLang expert can:[[1]](https://www.theladders.com/job/member-of-technical-staff-kernel-engineering-inferact-san-francisco-ca_87424404#1)[[5]](https://www.mycareersfuture.gov.sg/job/information-technology/member-technical-staff-kernel-engineering-inferact-singapore-e1cbf2522b5c6cf6d66e510c6930f402?source=MCF&event=RecommendedJobJD)

- Write high-performance kernels using TileLang
- Read and understand the generated underlying code (CUDA/HIP/Metal)
- Identify when automatic inference produces suboptimal results and correct them through scheduling annotations
- Reason about performance bottlenecks at the hardware level (memory bandwidth, instruction throughput, pipeline stalls)

This differs from traditional kernel engineers primarily in **the granularity of intervention**: the latter directly manipulates hardware resources, while the former guides the compiler's decisions. But the underlying hardware mental models—memory hierarchy, parallel execution, instruction characteristics—are shared.

So your judgment is half correct: TileLang experts indeed don't need to "go as bare metal" as traditional kernel engineers. But they are not completely detached from the metal either—they stand on a higher abstraction layer, using hardware knowledge to supervise and correct the compiler, rather than personally handling every detail.

---

## User

Right. I’m reminded that when DeepSeek R1 dropped, the team open-sourced their PTX tuning, if I recall correctly — or was that below the PTX level? And we don’t hear much about them having to do the equivalent now that they’re presumably optimizing for Ascend first, using CANN and TileLang in the process.

---

## DeepSeek

Your memory is accurate: the PTX tuning open-sourced by DeepSeek during the R1 period was indeed **below the CUDA C level, directly manipulating NVIDIA GPU assembly instructions**. As for why there is "not much noise" about Ascend now—that's because the nature of the work has changed: **they are no longer hand-writing underlying assembly, but rather building a reusable TileLang toolchain on Ascend**.

### The True Level of PTX Tuning: Below CUDA, Above Hardware

PTX is NVIDIA's **virtual instruction set** located below CUDA C/C++ and above SASS machine code. DeepSeek embedded inline PTX assembly in CUDA kernels at the time, with typical operations including streaming loads to bypass L1 cache pollution (`ld.global.cs`), native Tensor Core matrix multiply-accumulate, and warp-level shuffle instructions. This work is more low-level than ordinary CUDA kernel writing, directly controlling hardware cache behavior and instruction selection. In a sense, it is "hand-writing GPU assembly," but it remains within the NVIDIA ecosystem.[[1]](https://zhuanlan.zhihu.com/p/2020099024145924883#2)[[2]](https://cloud.tencent.cn/developer/article/2675223#6)-

### The Ascend Phase: From Hand-Written Assembly to Toolchain Output

The current situation is fundamentally different. According to publicly available information, DeepSeek's work on Ascend is centered on **TileLang and a series of open-source component libraries**, rather than hand-writing "Ascend PTX."

**The core tool is TileLang.** DeepSeek officially stated that the Ascend version of TileLang "encapsulates Ascend C low-level instructions, provides a high-level language programming approach, while not sacrificing hardware performance". This means developers use Python DSL to describe computations, and the compiler is responsible for generating efficient Ascend code. DeepSeek claims that "every TileLang operator used in DeepSeek training has a corresponding high-performance implementation on Ascend".[[7]](https://finance.sina.cn/2026-09-30/detail-initqkpm5828931.d.html?vt=4&wm=1943?wm1943)

**The work focus has shifted to system-level optimization.** Along with TileLang, they open-sourced DeepGEMM (matrix multiplication), DeepEP (communication), FlashMLA (attention), and other components, with performance "approaching hardware limits". But the focus of this work is making the toolchain and library run efficiently on Ascend, rather than hand-tuning every instruction like the PTX era.[[14]](https://www.c114.net.cn/industry/129232.html)

**There is an objective reason for the "lack of noise."** SemiAnalysis's analysis at the time pointed out that among the components open-sourced by DeepSeek, **only TileLang was in a usable state**, because DeepSeek required CANN 9.2.0 (not yet officially released) and a C++20 compiler, which the beta version did not provide at the time. The ecosystem is still being polished, and naturally there hasn't been the kind of explosive dissemination seen with R1's PTX at that time.[[3]](https://newsletter.semianalysis.com/p/huawei-deepseek)

### What This Means for Your Skill Path

The path you're interested in—TileLang-level expertise—is precisely the direction DeepSeek is following on Ascend. They use high-level DSL plus compiler to handle hardware details, while developers focus on scheduling and optimization decisions. Hand-writing PTX/assembly is a last resort when the toolchain is immature; as TileLang and CANN mature, the demand for "Ascend assembly" will decrease, while the value of engineers who understand hardware characteristics and can write efficient TileLang schedules will increase. This aligns with the positioning we discussed earlier: TileLang experts don't need to go as bare-metal as traditional kernel engineers, but they must understand the hardware well enough to guide the compiler.

---

## User

Suggest a comprehensive syllabus for a forward-looking beginner M5 MBP C++23 developer wanting to lean more toward TileLang and RISC-V in the AI accelerator industry. It would probably be best to include as many machine-learning and AI aspects as possible early in the course. Assume access to the ANE and simulators, but no Nvidia hardware or CUDA. The student is a 55-year-old retired Malaysian Chinese web developer with unlimited learning time who prefers each chapter to go deep instead of shallow and wide.

---

## DeepSeek

This syllabus is designed for your specific constraints: M5 MacBook Pro, no NVIDIA/CUDA, ANE access, unlimited time, and a preference for depth over breadth. The central thread is **AI as the workload**, **TileLang as the primary expression layer**, and **RISC-V as the hardware mental model** that makes you portable across the accelerators coming next. Each chapter is meant to be sat with until the underlying mechanism is genuinely understood, not merely completed.

### 🗺️ The Syllabus: From C++23 to Accelerator Portability

**Chapter 1: C++23 as a Systems Language (Deep Foundation)**

- **Core Focus**: Move beyond web-dev C++ habits. Master RAII, move semantics, templates, `constexpr`/`consteval`, and the memory model. The goal is to read and reason about code that manages hardware resources, not just application logic.
- **AI Connection**: Every kernel, runtime, and compiler backend you will touch is C++. Understanding object lifetimes and zero-overhead abstraction is the price of admission.
- **Resources**: The comprehensive guide by Torsten T. Will covers syntax through concurrency and best practices for modern C++ . Supplement with the Modern-CPP-Programming GitHub course for structured depth on templates and compile-time utilities .[[4]](https://www.sap-press.com/cpp_5927/?hss_channel=lcp-87081027&utm_campaign=Social%20-%20LinkedIn)[[10]](https://github.com/ljq/Modern-CPP-Programming#1)
- **M5 Exercise**: Write a C++23 program that allocates a buffer, performs a simple matrix multiply, and uses `std::execution` (or a thread pool) to parallelize it across cores. Profile it. Then rewrite it with `constexpr`-heavy metaprogramming to unroll the inner loop at compile time.

**Chapter 2: The Machine Learning Workload (From First Principles)**

- **Core Focus**: Build a small transformer from scratch in Python/PyTorch. Focus on the operations that matter for accelerators: GEMM, attention, normalization, and the memory-bound nature of inference.
- **AI Connection**: You cannot optimize what you do not understand. The goal is to know exactly what a "kernel" must compute before you learn how to write one efficiently.
- **Resources**: Sebastian Raschka's *Build a Large Language Model (From Scratch)* is the standard for coding a GPT-like model from the ground up .[[26]](https://github.com/mohd-faizy/full-stack-artificial-intelligence/blob/6abb935d6838b341d5332bf74995c8bcdb4ce2d0/66-AI-Learning-Repositories/LLM-Courses.md#1)
- **M5 Exercise**: Train a tiny GPT (e.g., 124M parameters or smaller) on a small text corpus using PyTorch MPS. Profile where time goes. Identify the operations that dominate latency and memory bandwidth.

**Chapter 3: TileLang Fundamentals (The Portable Kernel Layer)**

- **Core Focus**: Install TileLang with the Metal backend on your M5. Learn the `@tilelang.jit` decorator, `T.prim_func`, `T.Kernel` context, and the separation of dataflow from scheduling.
- **AI Connection**: This is your primary tool for writing accelerator code without CUDA. The Metal backend is supported and validated on M5 systems, with performance competitive with MLX on GEMM workloads .[[15]](https://github.com/tile-ai/tilelang/blob/f3544306/docs/compiler_internals/metal_tilelang_development.md?plain=1#1)[[22]](https://github.com/tile-ai/tilelang/blob/752312c2a92ed9318789391ff69454b160bd4904/README.md)
- **Resources**: The TileLang quick start documentation walks through a vector addition kernel and explains the compilation chain . The broader AI-infra plugin reference covers tensor interoperability, pipelining, and profiling .[[1]](https://github.com/jstzwj/ai-infra-plugins/blob/main/plugins/tilelang/skills/tilelang/references/02-getting-started.md#1)[[7]](https://raw.githubusercontent.com/jstzwj/ai-infra-plugins/refs/heads/main/plugins/tilelang/skills/tilelang/references/02-getting-started.md#2)
- **M5 Exercise**: Write a TileLang kernel for element-wise addition targeting `metal`. Then write a tiled GEMM kernel. Compare its performance against PyTorch MPS and MLX on your M5. The goal is not to beat them immediately, but to understand *why* TileLang's generated code performs the way it does .[[15]](https://github.com/tile-ai/tilelang/blob/f3544306/docs/compiler_internals/metal_tilelang_development.md?plain=1#1)

**Chapter 4: Compiler Infrastructure (TVM and MLIR)**

- **Core Focus**: Understand what happens beneath TileLang. Learn TVM's TIR, lowering passes, and the MLIR dialect ecosystem. Trace a TileLang kernel through the compilation pipeline.
- **AI Connection**: TileLang is built on TVM. The ability to debug and extend the compiler is what separates a user from an expert. This is also the layer that translates high-level models to RISC-V-based accelerator instructions.
- **Resources**: The TVM/MLIR deep practice guide explains lowering, operator fusion, and autotuning from a systems perspective . Read the TileLang Metal backend internals documentation to see how lowering decisions (shared staging bypass, simdgroup cooperative tensors) affect performance on your M5 .[[3]](https://github.com/datawhalechina/llm-algo-leetcode/blob/main/docs/01_Hardware_Math_and_Systems/32_TVM_MLIR_Deep_Practice.md#1)[[27]](https://github.com/tile-ai/tilelang/blob/752312c2a92ed9318789391ff69454b160bd4904/docs/compiler_internals/metal_tilelang_development.md)
- **M5 Exercise**: Modify a TileLang kernel's schedule (e.g., block size, pipeline stages) and inspect the generated Metal code. Try to intentionally trigger a suboptimal lowering path and then fix it through scheduling annotations. Read the Metal codegen source in the TileLang repository.

**Chapter 5: RISC-V as the Accelerator Mental Model**

- **Core Focus**: Learn RISC-V assembly, the ISA, and the toolchain. Focus on the concepts that transfer to any accelerator: explicit register allocation, load/store architecture, and vector extensions.
- **AI Connection**: RISC-V is the ISA of Tenstorrent's AI accelerators and the foundation for many emerging designs. Understanding it makes you fluent in the "instruction set" layer of any new chip.
- **Resources**: The official RISC-V learning path recommends starting with assembly fundamentals (Easy RISC-V, RARS simulator) and progressing to toolchains (GNU Toolchain, QEMU) . The *RISC-V Reader* is the conceptual anchor.[[2]](https://raw.githubusercontent.com/riscv/learn/refs/heads/main/README.md#1)
- **M5 Exercise**: Write a RISC-V assembly program that performs a vector dot product. Run it in RARS or QEMU. Then write the same operation in TileLang targeting Metal. Compare the level of control each abstraction gives you over memory movement and arithmetic.

**Chapter 6: The Apple Neural Engine as an "Unknown Newcomer"**

- **Core Focus**: Use ANEForge to compile a small model directly to the ANE, bypassing Core ML's scheduler. Measure dispatch overhead, operator eligibility, and energy consumption.
- **AI Connection**: This is your hands-on "new accelerator" exercise. The ANE has a compile-then-dispatch model, fixed weight baking, and an opaque ISA. Learning to optimize for it teaches you how to reason about *any* constrained NPU.
- **Resources**: ANEForge provides a Python interface to the ANE, with benchmarks showing its performance and energy efficiency relative to the GPU on M-series chips . The Orion paper describes the ANE's constraints (convolution engine, compile-time weight baking, CPU/ANE division of labor) in detail .[[5]](https://arxiv.org/html/2603.06728v1#2)[[19]](https://pypi.org/project/aneforge/0.3.0/#1)
- **M5 Exercise**: Convert a 1B parameter model to ANEForge. Profile the prefill and decode phases. Identify which operations fall back to the CPU and why. Then try to restructure the model to increase ANE residency (e.g., fusing ops, changing precision).

**Chapter 7: Portable Accelerator Programming with Tenstorrent (Simulator)**

- **Core Focus**: Use the Wolfpine simulator for Tenstorrent's tt-metal stack. Write a tt-metal program and run it against a simulated Blackhole or Wormhole accelerator.
- **AI Connection**: Tenstorrent's architecture is RISC-V-based, open-source, and explicitly targets AI workloads. The simulator lets you practice the "porting to a new chip" workflow without buying hardware .[[6]](https://pypi.org/project/wolfpine/2.2/#files#1)
- **Resources**: Wolfpine is installable via pip and runs tt-metal programs without modification, setting the necessary environment variables for simulation .[[6]](https://pypi.org/project/wolfpine/2.2/#files#1)
- **M5 Exercise**: Follow the Wolfpine examples to write a simple tt-metal kernel. Run it in simulation. Compare its programming model (RISC-V cores, explicit data movement) to TileLang's abstraction. Document the conceptual mapping between TileLang's tiling and Tenstorrent's core grid.

**Chapter 8: The Full Stack Capstone**

- **Core Focus**: Take a small model (e.g., Qwen3-0.6B or a tiny GPT), implement a critical operation (e.g., attention or RMSNorm) in TileLang for Metal, benchmark it on your M5, and write a technical report analyzing the performance characteristics.
- **AI Connection**: This is the portfolio piece. It demonstrates that you can go from a model requirement to a hand-optimized kernel on a non-NVIDIA backend, measure it rigorously, and explain the bottlenecks.
- **M5 Exercise**: Deliverable: A GitHub repository with the TileLang kernel, benchmarking scripts, a comparison against PyTorch MPS and MLX, and a write-up of the roofline analysis (memory bandwidth vs. compute limits). This is the artifact that proves you can do the work, not just talk about it.

### 💎 How to Approach This

Each chapter should be treated as a **deep dive**, not a checklist item. If Chapter 3 (TileLang) takes a month of daily experimentation, that is time well spent. The goal is not to "finish" the syllabus, but to emerge with the ability to look at any new accelerator and reason about how to map an AI workload onto it, using the tools and mental models you have built. Your M5 is not a limitation; it is a controlled laboratory for the exact skills that are becoming scarce.
