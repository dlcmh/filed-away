# TileLang and the new wave of AI compute DSLs

> Why "tile" in TileLang is no coincidence, how new TileLang is, and why PyTorch and CUDA never had AI compute sewn up
>
> Source: [shared conversation](https://chat.deepseek.com/share/5hs5mqyckc5jt9dvke) on chat.deepseek.com. 4 questions, 4 answers. The source link expires when the conversation is deleted from DeepSeek.
> Recovered from the shared-conversation HTML export: tables and web citations preserved.

---

## User

reading through https://sota-ai.pages.dev/ch04-cache-optimized-matmul now, there's the word "tile" - is "Tile" in TileLang merely coincidental to the word "tile" in this chapter?

---

## DeepSeek

Based on the provided chapter on cache-optimized matrix multiplication, the use of the word "tile" in this context is **not at all coincidental** with the concept of a "Tile" in TileLang. The fundamental idea is the same, though applied at different levels of the computing stack.

Here’s a breakdown of the connection:

### The Shared Core Concept

In the chapter, **"tiling"** (or blocking) is a **software optimization technique**. It involves breaking down a large matrix multiplication operation into smaller sub-matrix multiplications called **"tiles"** (or blocks). The goal is to ensure that the data for a tile from matrix `A` and a tile from matrix `B` fit into the fast CPU cache (like L1 or L2) so that the CPU can access them much faster than if it had to keep fetching from the slower main memory (RAM).

### Connection to TileLang

**TileLang** is a domain-specific language for generating high-performance code, often for hardware accelerators like GPUs or CPUs. The term "Tile" in TileLang refers to a similar concept but at a **hardware or compiler level**:

1. **Tile as a Language Primitive**: In TileLang, a `Tile` is often a built-in data structure or a compiler directive that explicitly describes a block of data that will be processed together. It is a first-class citizen in the language's type system.
2. **Hierarchical Tiling**: TileLang usually allows for **hierarchical tiling**, where you can define tiles for different levels of the memory hierarchy. For example:
   - You might define a **large tile** that fits in the L2 cache.
   - Inside that, you define a **smaller tile** that fits in the L1 cache or in the shared memory of a GPU.
   - This mirrors the chapter's discussion of choosing a `block_size` based on cache sizes but makes it a more explicit, programmable concept.

### Summary of the Relationship

| Feature | Cache-Optimized Matmul (Chapter 4) | TileLang (Conceptually) |
| --- | --- | --- |
| **Level** | Software-level algorithm optimization | Programming language / compiler-level abstraction |
| **Purpose** | To reorganize loops for better CPU cache utilization. | To provide a language construct for describing blocked/tiled computations, making optimizations explicit and portable. |
| **Mechanism** | The programmer manually chooses `block_size` and restructures loops (`i, k, j` order). | The language provides `Tile` types and operations, and the compiler handles loop generation and memory management. |
| **"Tile" Meaning** | A sub-matrix (a block of data) used in the computation. | A fundamental data type or compilation unit representing a block of data to be processed. |

**In essence:** The chapter explains the *why* and *how* of tiling as a manual optimization. TileLang then takes this proven concept and embeds it as a core language feature, allowing developers to express tiled algorithms more naturally and efficiently across different hardware, without writing the low-level loop-nesting code every time.

In short, the word "tile" in TileLang is a **direct and deliberate reference** to the tiling technique you are reading about. The language is named to emphasize that it is designed to make tiled, cache-aware programming a primary feature.

---

## User

TileLang is quite new isn't it?

---

## DeepSeek

是的，TileLang 是一个非常新的技术项目。从它在学术圈正式亮相、在开源社区发布，到获得行业认可和采用，这一切都发生在最近一两年内。

这个项目虽然新，但发展非常迅速，可以从下面几个方面看到它的"新"：

- **正式提出与开源**：TileLang 由北京大学计算机学院团队主导开发，其学术论文在2025年才正式发表[[11]](https://ar5iv.labs.arxiv.org/html/2504.17577)。项目也在 **2025年1月** 于GitHub上正式开源[[2]](https://baike.baidu.com/item/TileLang/67440655?fromModule=lemma_inlink)[[5]](https://stock.finance.sina.com.cn/stock/view/paper.php?symbol=sh000001&reportid=813835231666&autocallup=no&isfromsina=no)[[7]](https://hub.baai.ac.cn/view/49358)。
- **快速获得业界关注**：尽管诞生时间不长，TileLang 已因其潜力获得了产业界的重视。例如，**DeepSeek-V3** 这样的大型模型在研发中就采用了TileLang进行算子开发与性能验证[[1]](https://m.cnstock.com/commonDetail/637397)[[3]](https://m.163.com/dy/article/KLFRQL7O0511CPVM.html?spss=adap_pc)[[7]](https://hub.baai.ac.cn/view/49358)。
- **生态正在蓬勃发展**：从2025年底到2026年初，TileLang的生态出现了显著增长。包括**摩尔线程**、**华为昇腾**、**海光DCU**在内的多家国内芯片厂商和平台，都陆续宣布对TileLang提供支持或完成适配[[1]](https://m.cnstock.com/commonDetail/637397)[[7]](https://hub.baai.ac.cn/view/49358)[[8]](http://kjj.gz.gov.cn/xydt/content/post_10688537.html)。其PyPI包的第一个版本发布也大约是在一年前[[6]](https://packages.ecosyste.ms/registries/pypi.org/packages/tilelang/versions)，截至2026年6月，GitHub仓库已发布了包括v0.1.11在内的多个迭代版本[[4]](https://github.com/tile-ai/tilelang?ref=dailydev)，这些都印证了其作为新生项目的活跃度。

总而言之，TileLang是一个在 **2025年初才崭露头角的新兴项目**。它通过将你正在学习的"分块"（tiling）思想作为语言的核心抽象，旨在简化高性能AI算子的开发。尽管年轻，它已经展现出强大的生命力，并正在快速构建起自身的生态[[1]](https://m.cnstock.com/commonDetail/637397)[[8]](http://kjj.gz.gov.cn/xydt/content/post_10688537.html)[[10]](https://github.com/tile-ai/tilelang-ascend/releases)。

---

## User

Opps kindly translate all that into English

---

## DeepSeek

You're right, my apologies! Here's the full response in English:

---

Yes, **TileLang is indeed a very new technology**. Its official academic debut, open-source release, and initial industry adoption have all occurred within the last year or two.

While young, the project is developing rapidly. Here’s a breakdown of just how new it is:

- **Formal Introduction & Open-Sourcing**: TileLang was developed by a team at Peking University's School of Computer Science. Its academic paper was officially published in **2025**, and the project was open-sourced on GitHub in **January 2025**.
- **Rapid Industry Attention**: Despite its short existence, TileLang has already garnered significant interest from the industry due to its potential. For example, large-scale models like **DeepSeek-V3** adopted TileLang for operator development and performance verification during their R&D.
- **A Thriving Ecosystem**: From late 2025 into 2026, TileLang's ecosystem has seen notable growth. Multiple domestic Chinese chip manufacturers and platforms, including **Moore Threads**, **Huawei Ascend**, and **Hygon DCU**, have announced support for or adaptation to TileLang. Its first PyPI package release was roughly a year ago, and as of June 2026, the GitHub repository has seen multiple iterative releases (including v0.1.11), all confirming its status as a vibrant new project.

In summary, TileLang is an **emerging project that only came into the spotlight around early 2025**. It takes the "tiling" concept you're learning about and makes it a core language abstraction to simplify high-performance AI operator development. Despite being young, it shows strong momentum and is rapidly building its own ecosystem.

---

## User

blows the mind that new ways of scratching compute "itches" are still being invented today - I thought PyTorch and CUDA had these all sewn up - please explain

---

## DeepSeek

It's a fantastic observation, and you're right to be surprised! It *does* feel like PyTorch and CUDA should have "sewn up" the world of AI compute.

To understand why new projects like TileLang are still emerging, it helps to think of the AI computing landscape not as a finished skyscraper, but as a bustling, ever-expanding city. PyTorch and CUDA are the massive downtown skyscrapers—essential and dominant—but they don't cover every neighborhood.

Here is why new "compute itches" keep appearing:

### 1. PyTorch and CUDA play completely different roles

First, it's crucial to separate them:

- **CUDA (and NVIDIA's hardware)** is the **foundation**. It's the low-level language and instruction set for NVIDIA GPUs. It's the "dirt and concrete" of the city.
- **PyTorch** is the **high-level framework**. It's the "architect's blueprint" that researchers use to design neural networks without worrying about the dirt and concrete.

The problem? **CUDA is tied exclusively to NVIDIA hardware**, and PyTorch is deeply dependent on CUDA. For years, if you wanted to train large AI models, you *had* to use NVIDIA GPUs.

### 2. The Hardware Monopoly is Shattering

For over a decade, NVIDIA reigned supreme, so CUDA became the default. But today, the landscape is fragmenting:

- **AMD** is gaining traction with its ROCm software stack.
- **Intel** is pushing its Gaudi accelerators and GPUs.
- **Tech giants** (Google with TPUs, Amazon with Trainium, Microsoft with Maia) are building their own custom chips.
- **Chinese companies** (Huawei Ascend, Moore Threads, Hygon DCU) are developing domestic GPUs.

Here’s the itch: If you write your AI kernel (a piece of math code) in **CUDA**, it **only runs on NVIDIA chips**. To run on AMD, Intel, or Huawei, you have to rewrite that kernel in their proprietary languages (ROCm, SYCL, etc.). That is an enormous, expensive headache. TileLang is a **new "universal translator"**—you write the math once in TileLang, and its compiler can generate code for *multiple* hardware backends.

### 3. The End of "Free" Performance (The End of Dennard Scaling)

For decades, chipmakers just made transistors smaller and smaller, so your PyTorch code automatically got faster on new NVIDIA GPUs without you changing a line. **That era is over.**

Today, raw clock speeds aren't increasing much. Instead, chips get faster by becoming more **specialized** and **parallel**. To get the last 2x–5x of performance out of a modern chip, you have to deeply understand its cache hierarchy, its memory bandwidth, and its tensor cores.\
Writing highly optimized CUDA code to squeeze out this performance is *incredibly* difficult—it's often called "expert-level black magic." TileLang is an **itch-scratcher** that automates this dark art. It lets you tell the compiler, "Here is my math, and here is my tiling strategy," and the compiler figures out the hyper-optimized, low-level CUDA/HIP/SYCL code for you.

### 4. The Math Itself is Changing Fast

PyTorch is great for standard stuff (matrix multiplies, convolutions, ReLUs). But AI researchers are constantly inventing new operations:

- **State Space Models** (like Mamba)
- **Mixture of Experts** (routing)
- **Quantized / Low-precision arithmetic** (FP8, INT4)
- **Custom attention mechanisms**

PyTorch has to play catch-up. For these brand-new operations, researchers often have to write custom CUDA kernels from scratch, which slows down research. A new language like TileLang, which is designed from the ground up for **flexible, composable tensor operations**, gives researchers a faster way to prototype novel math and get near-peak hardware performance without becoming CUDA experts.

### 5. The "Approximate" vs. "Exact" Compute Shift

Traditional computing is about *exact* answers (1+1=2). AI is fundamentally different—it's about *approximate* answers (probabilities, matrices, tensors).

We are realizing that we don't need 64-bit (double) or even 32-bit (float) precision for most AI tasks. We can use 8-bit, 4-bit, or even 1-bit numbers. CUDA was designed for exact, high-precision scientific computing. New languages like TileLang are being built *specifically* for the probabilistic, low-precision world of AI, with new data types and math tricks baked into the language itself.

---

### The Big Picture

| Era | Problem | Solution |
| --- | --- | --- |
| **2007–2020** | "We need a way to do massive parallel math on GPUs." | **CUDA** becomes the standard. |
| **2016–Present** | "We need an easy way to build neural networks without writing CUDA." | **PyTorch / TensorFlow** abstract the hardware. |
| **2023–Future** | "We need to run AI on **any** chip, at **maximum** speed, for **new** math, without rewriting everything for each vendor." | **New languages like TileLang, Triton, and Mojo** are the emerging answer. |

In short: PyTorch and CUDA "sewed up" the **old** problem (how to do deep learning on NVIDIA GPUs). But the **new** problems (multi-vendor hardware, the end of free performance boosts, and rapidly evolving AI math) have created a whole new set of "itches" that require fundamentally new tools to scratch. We are right in the middle of another major shift in how AI software is written!
