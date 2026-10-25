# An engine-free C++ graphics roadmap: stages, books, and resources

> Based on a long DeepSeek conversation about learning game and graphics programming without a game engine: [shared conversation](https://chat.deepseek.com/share/cgxm9z20u1lmqynire). This article extracts the roadmap, books, and resources; personal background and motivational commentary are omitted.

The sequence is deliberately bottom-up: C++ and headless game logic first, then mathematics and software architecture, then the rendering pipeline, then explicit GPU APIs and the engine subsystems that sit around rendering. The order is more important than the pace. Each stage produces a project that exercises the previous stage.

## The path in one view

| Stage | Focus | Main resources |
| --- | --- | --- |
| 1 | Modern C++ and headless game logic | *Programming: Principles and Practice Using C++*; *C++ Primer*; *Beginning C++ Game Programming*; *Game C++ Programming: A Practical Introduction* |
| 2 | Mathematics and software architecture | *Computer Graphics: From Pixels to Programmable Graphics Hardware*; *Geometry for Programmers*; *Mathematics for Game Programming and Computer Graphics*; *Entity-Component System Design Patterns* |
| 3 | Rendering pipeline | *Beginning C++ Game Programming* (later chapters); *Computer Graphics: From Pixels to Programmable Graphics Hardware*; *Real-Time Rendering*; *Computer Graphics Programming in OpenGL with C++*; *Computer Graphics Through OpenGL* |
| 3.5 | Explicit graphics APIs | Khronos Vulkan tutorial; Apple Metal documentation; Vulkan-Hpp; VMA; GLFW or SDL3; GLM |
| 4 | Physics and collision | *Game Physics Cookbook*; *Real-Time Collision Detection* |
| 5 | Animation | *Game Animation Programming with C++*; *Modern Game Animation in C++* |
| 6 | Advanced rendering, ray tracing, virtualized geometry | *Real-Time Rendering*; *GPU Pro* / *ShaderX*; *Real-Time Ray Tracing with DirectX 12 (DXR)*; Epic Nanite documentation; Nyx |
| 7 | Audio and networking | *Game Audio Programming 5*; Unity *Multiplayer Networking* e-book |
| Elective | Neural rendering | Iowa State “3D Vision — NeRFs and INRs”; Instant-NGP and 3D Gaussian Splatting papers; Neural-Rendering-Engine |

## Stage 1: C++ and headless game logic

The first stage is language and program design, not graphics. The source recommends a systematic C++ text before game-specific material:

- *Programming: Principles and Practice Using C++* by Bjarne Stroustrup.
- *C++ Primer* for modern C++ after C++11.
- *Beginning C++ Game Programming* (3rd edition, 2024), which uses SFML for small projects and covers C++ basics, object-oriented design, pointers, the STL, and collision detection.
- *Game C++ Programming: A Practical Introduction*, which builds games without an engine or graphics library.

The practical exercise is a console Space Invaders: a character grid, a small set of entities, collision checks, and a loop that processes input, updates state, and presents the grid. The point is to establish the separation between game logic and presentation before any GPU code is introduced.

## Stage 2: Mathematics and software architecture

The mathematical foundation is vectors, matrices, quaternions, curves, and surfaces. The architectural foundation is data layout and entity organization.

- *Computer Graphics: From Pixels to Programmable Graphics Hardware* covers the vector, matrix, and quaternion foundations, along with splines, curves, and surfaces.
- *Geometry for Programmers* is a practical treatment of splines and geometric transformations, using Python examples and assuming only high-school mathematics.
- *Mathematics for Game Programming and Computer Graphics* covers vectors, matrices, meshes, and vertex shaders through Python and PyOpenGL.
- *Entity-Component System Design Patterns* (2025) covers ECS theory, storage models, and data locality.
- Khronos Vulkan tutorial, [Data-oriented design appendix](https://github.khronos.org/Vulkan-Site/tutorial/latest/Building_a_Simple_Engine/Appendix/appendix.html#data-oriented-design), for a free architectural reference.

This is also the stage for data-oriented design: contiguous component storage, systems that iterate over components, and the difference between an object model and a data layout. The source places ECS here because it determines the performance ceiling of the game-logic layer, not just the rendering layer.

## Stage 3: The rendering pipeline

The first rendering goal is a triangle, not a game. The source’s sequence is window creation, shader compilation, vertex data, and a draw call, followed by textures and lighting.

- *Beginning C++ Game Programming* covers vertex arrays and OpenGL shaders in its later chapters.
- *Computer Graphics: From Pixels to Programmable Graphics Hardware* uses OpenGL 3.3+ and progresses from basic rendering to animation, lighting, and bump mapping.
- *Real-Time Rendering* (4th edition) is a reference, not a linear tutorial.
- *Computer Graphics Programming in OpenGL with C++* (third edition) covers 3D data, textures, parametric surfaces, and ray tracing with bounding volume hierarchies.
- *Computer Graphics Through OpenGL* is a broader, more academic alternative with many programs and experiments.
- *Focus on Curves and Surfaces* is a focused treatment of Bezier curves, B-splines, and NURBS.
- A minimal OpenGL triangle walkthrough: [KU OpenGL example](https://people.eecs.ku.edu/~jrmiller/Courses/OpenGL/HelloOpenGL/HelloOpenGLBasic/HelloOpenGLBasic.html).

A useful checkpoint is a renderer that draws the same entity positions used by the console game. That demonstrates that the game logic is independent of the presentation layer.

## Stage 3.5: Explicit graphics APIs

OpenGL hides memory management, synchronization, and pipeline state. Vulkan and Metal expose them. The source recommends inserting this stage after OpenGL rather than replacing it.

Vulkan resources:

- Khronos’s official Vulkan tutorial at `docs.vulkan.org`.
- `vulkan-tutorial.com` as a secondary tutorial, with attention to whether it targets Vulkan 1.0 or a more modern version.
- GLFW or SDL3 for windowing and input.
- GLM for mathematics.
- Vulkan-Hpp for C++ bindings.
- Vulkan Memory Allocator (VMA) for allocation.

Metal resources:

- Apple’s “Drawing a triangle with Metal 4.”
- Apple’s “Performing calculations on a GPU.”
- Metal Shading Language documentation.

The mental shift is from “draw this” to “record a command buffer, configure pipeline state, bind resources, submit to a queue, and synchronize with a fence.” The added verbosity buys explicit control over memory and scheduling.

## Stage 4: Physics and collision

- *Game Physics Cookbook* builds a rigid-body engine from linear algebra, covering primitive intersection tests, particles, rigid bodies, and soft bodies. The source notes that its simplified solver omits an arbiter and can produce excessive sliding; it is still useful for understanding the pipeline.
- *Real-Time Collision Detection* is the advanced reference for robustness, numerical precision, and optimization.

The implementation order is broad phase, narrow phase, contact generation, and constraint resolution. A simple sphere-sphere or AABB test is sufficient before adopting a library such as Bullet or Jolt.

## Stage 5: Animation

- *Game Animation Programming with C++* (2025) covers skeletal animation with Assimp, GPU skinning, inverse kinematics, blend trees, and a third-person character case study.
- *Modern Game Animation in C++* (2025) covers similar ground with an emphasis on integration with ECS and rendering pipelines.
- Khronos Vulkan tutorial, [Skeletal compute skinning](https://github.khronos.org/Vulkan-Site/tutorial/latest/Advanced_glTF/Skeletal_Compute_Skinning/06_conclusion.html), for a GPU-side reference implementation.

Both titles are independently published; preview the table of contents before purchase. The technical sequence is bone hierarchies, inverse bind matrices, linear blend skinning, dual-quaternion skinning, animation state machines, and inverse kinematics.

## Stage 6: Advanced rendering, ray tracing, and virtualized geometry

- *Real-Time Rendering* remains the reference for the principles.
- *GPU Pro* and *ShaderX* contain articles on ray tracing and shader techniques; some volumes are free.
- *Real-Time Ray Tracing with DirectX 12 (DXR)* covers reflection, refraction, and transparent materials with hardware-accelerated ray tracing. The algorithms transfer conceptually to Vulkan ray tracing.
- Nanite has no dedicated book. Epic’s official Nanite documentation is the reliable source.
- Nyx, an open-source Nanite-style renderer, is useful for studying cluster hierarchy, visibility buffers, and GPU-driven culling.
- UCSD CSE 272, [Nanite lecture](https://cseweb.ucsd.edu/~tzli/cse272/wi2025/lectures/27_nanite.pdf).
- Illinois CS 415, [Nanite slides](https://raw.githubusercontent.com/illinois-cs415/illinois-cs415.github.io/main/img/slides/415-NaniteUE5.pdf).

Nanite is best treated as an advanced system to understand after writing a rasterizer. Its core ideas are cluster hierarchies, screen-space error thresholds, a visibility buffer, deferred material evaluation, and GPU-driven culling.

## Stage 7: Audio and networking

- *Game Audio Programming 5* (2025) covers low-level oscillators, asynchronous multithreaded audio engines, speech systems, and mixing. [Publisher page](https://www.taylorfrancis.com/books/edit/10.1201/9781003519119/game-audio-programming-5-guy-somberg).
- Epic Games, [Audio Gameplay Volumes](https://dev.epicgames.com/documentation/unreal-engine/audio-gameplay-volumes-overview), for a production example of spatial audio and volume handling.
- Unity’s [Multiplayer Networking e-book](https://unity.com/blog/multiplayer-networking-ebook) covers UDP, RPCs, client-side prediction, server reconciliation, rollback, and deterministic physics. The concepts are engine-agnostic even though the examples are Unity-oriented.

Audio and networking are independent subsystems. They can be deferred until the game actually needs sound or multiplayer, but their architectural constraints should be known before the engine’s data model is fixed.

## Elective: Neural rendering

NeRF and 3D Gaussian Splatting are not replacements for the rasterization path; they are an alternative scene representation built on GPU compute and, for NeRF, neural networks.

Courses:

- Iowa State’s “3D Vision — NeRFs and INRs” course is free, requires basic Python and PyTorch, and covers 3D representations, NeRF, and 3DGS with coding assignments.
- Deep Blue Academy (Shenlan) offers a paid Chinese-language course, “NeRF and 3D Gaussian Splatting: Fundamentals and Common Algorithms”, taught by a professor from Beijing University of Posts and Telecommunications. It runs for more than 13 hours and includes paper walkthroughs and code practice: [course page](https://www.shenlanxueyuan.com/course/661).

Papers and implementations:

- The [Instant-NGP paper](https://arxiv.org/abs/2201.05989) covers multi-resolution hash encoding.
- The [3D Gaussian Splatting paper](https://arxiv.org/abs/2308.04079) covers explicit Gaussian primitives and splatting.
- [Neural-Rendering-Engine](https://github.com/Custardtart77/Neural-Rendering-Engine) is a Vulkan-based implementation useful for studying the engineering structure.

The prerequisites are GPU compute, ray marching, and a basic understanding of MLPs and backpropagation. This belongs after the Vulkan compute and ray-tracing material, not in the middle of the rasterization stage.

## Platform track: Vulkan, Metal, and HarmonyOS

Vulkan is the cross-platform baseline. Metal is the Apple-specific path. HarmonyOS Next is best treated as a Vulkan ecosystem with Huawei-specific extensions, not as a fourth foundational API.

HarmonyOS-specific additions:

- [Vulkan on HarmonyOS overview](https://developer.huawei.com/consumer/cn/doc/doccenter-references/api/vulkan-overview) and [Vulkan reference](https://developer.huawei.com/consumer/cn/doc/harmonyos-references/vulkan); includes `VK_OHOS_surface` and `VK_OHOS_external_memory` for window surfaces and zero-copy external memory.
- Node-API bridging between ArkTS and C/C++.
- [XEngine Kit](https://developer.huawei.com/consumer/en/doc/Tools-Guides/xengine-kit-0000002030297201) for spatial upscaling and adaptive variable-rate shading.
- [Graphics Accelerate Kit](https://developer.huawei.com/consumer/en/doc/harmonyos-guides/graphics-accelerate-fg-mv-vulkan) for frame generation and related optimizations.
- [OpenGTX C++ example](https://developer.huawei.com/consumer/cn/codelabsPortal/carddetails/tutorials_OpenGTX) for end-to-end integration.

This track is platform work, not a replacement for the rendering fundamentals.

## Engine-first alternatives

If the constraint is engine-based development rather than engine-free C++, the source suggests choosing one engine and one project:

- Unity: *C# and Unity 6 for Beginners*; *Unity 6 Game Programming with C#*.
- Godot: *Godot 4 Game Development with GDScript 2.0*; *Godot Game Development Mastery*.
- Unreal: *C++ Game Programming with Unreal Engine*; *Unreal Engine 5 Game Programming*.

The engine-free path and the engine-first path answer different requirements. Mixing them at the start adds tooling overhead without strengthening the lower-level model.

## How to sequence the work

- Start with a console game before a graphics window.
- Draw a triangle before drawing a game.
- Reuse the console game’s state when moving to OpenGL; only the presentation layer should change.
- Treat *Real-Time Rendering* and *Game Engine Architecture* as reference manuals, not cover-to-cover reads.
- After OpenGL, implement one triangle in Vulkan before adding abstraction layers.
- Add physics, animation, audio, and networking when a project needs them, not because the roadmap lists them.

## General reference

*Game Engine Architecture* by Jason Gregory is a reference manual for engine subsystems rather than a linear tutorial. It is useful when a project reaches resource management, the game loop, rendering devices, or subsystem boundaries.

## Industry take: where demand is likely to grow

These are judgments about the direction of the field, not claims taken from the source conversation.

**Explicit GPU API work is becoming specialist work.** Vulkan, Metal, and D3D12 expertise is concentrated in engine, platform, and graphics-tooling teams rather than in every gameplay role. The demand is narrower but deeper: synchronization, memory aliasing, pipeline caching, and GPU captures matter more than knowing the API entry points.

**GPU-driven rendering is moving from engine-specific to general practice.** Nanite popularized cluster hierarchies, visibility buffers, and indirect GPU scheduling. Similar ideas are appearing in other engines and in API features such as work graphs. The transferable skills are compute shaders, indirect draws, bindless resource tables, and profiling.

**Neural rendering is in an early production phase.** Gaussian Splatting and NeRF are finding use in capture, virtual production, e-commerce, digital twins, and simulation. The near-term demand is less for research scientists than for engineers who can integrate a neural representation into an existing renderer, manage GPU memory, and preserve real-time performance. Rasterization remains the base layer.

**WebGPU is an emerging portability target.** It brings compute and modern GPU concepts to the browser and to web-based tools. It is unlikely to replace native Vulkan or Metal for high-end engines, but it is relevant for visualization, editors, and cross-platform tooling.

**Platform-specific graphics stacks remain valuable.** Apple’s Metal ecosystem and Huawei’s HarmonyOS graphics stack create demand for engineers who can map a Vulkan-era mental model onto vendor extensions, platform bridges, and vendor toolkits. Vulkan remains the common conceptual substrate.

**Performance tooling is underrated.** As hardware and API diversity increase, the ability to read a GPU capture, identify a pipeline stall, and explain a frame’s cost is more durable than knowledge of any single API’s boilerplate.

## Resource notes

- Several 2025 animation and rendering titles are independently published; check the table of contents and sample chapters before relying on them.
- Regional bookstore links in the source are not reproduced here. The book titles are the durable reference; availability varies by region.
- Official documentation should outrank third-party summaries for Vulkan, Metal, Nanite, and HarmonyOS.

## References

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/cgxm9z20u1lmqynire).
- Khronos, [Vulkan documentation](https://docs.vulkan.org/).
- Khronos, [Data-oriented design appendix](https://github.khronos.org/Vulkan-Site/tutorial/latest/Building_a_Simple_Engine/Appendix/appendix.html#data-oriented-design).
- Khronos, [Skeletal compute skinning](https://github.khronos.org/Vulkan-Site/tutorial/latest/Advanced_glTF/Skeletal_Compute_Skinning/06_conclusion.html).
- KU, [Hello OpenGL example](https://people.eecs.ku.edu/~jrmiller/Courses/OpenGL/HelloOpenGL/HelloOpenGLBasic/HelloOpenGLBasic.html).
- Apple, [Metal documentation](https://developer.apple.com/documentation/metal).
- Epic Games, [Nanite virtualized geometry](https://dev.epicgames.com/documentation/unreal-engine/nanite-virtualized-geometry-in-unreal-engine).
- UCSD CSE 272, [Nanite lecture](https://cseweb.ucsd.edu/~tzli/cse272/wi2025/lectures/27_nanite.pdf).
- Illinois CS 415, [Nanite slides](https://raw.githubusercontent.com/illinois-cs415/illinois-cs415.github.io/main/img/slides/415-NaniteUE5.pdf).
- Epic Games, [Audio Gameplay Volumes](https://dev.epicgames.com/documentation/unreal-engine/audio-gameplay-volumes-overview).
- Unity, [Multiplayer Networking e-book](https://unity.com/blog/multiplayer-networking-ebook).
- Taylor & Francis, [Game Audio Programming 5](https://www.taylorfrancis.com/books/edit/10.1201/9781003519119/game-audio-programming-5-guy-somberg).
- Huawei, [Vulkan on HarmonyOS overview](https://developer.huawei.com/consumer/cn/doc/doccenter-references/api/vulkan-overview).
- Huawei, [Vulkan reference](https://developer.huawei.com/consumer/cn/doc/harmonyos-references/vulkan).
- Huawei, [XEngine Kit](https://developer.huawei.com/consumer/en/doc/Tools-Guides/xengine-kit-0000002030297201).
- Huawei, [Graphics Accelerate Kit](https://developer.huawei.com/consumer/en/doc/harmonyos-guides/graphics-accelerate-fg-mv-vulkan).
- Huawei, [OpenGTX C++ example](https://developer.huawei.com/consumer/cn/codelabsPortal/carddetails/tutorials_OpenGTX).
- Iowa State University, [3D Vision — NeRFs and INRs](https://trac-ai.iastate.edu/event/3d-vision-nerfs-and-inrs-2/).
- Deep Blue Academy, [NeRF and 3D Gaussian Splatting: Fundamentals and Common Algorithms](https://www.shenlanxueyuan.com/course/661).
- Instant-NGP, [Multi-resolution hash encoding](https://arxiv.org/abs/2201.05989).
- 3D Gaussian Splatting, [Real-time radiance field rendering](https://arxiv.org/abs/2308.04079).
- GitHub, [Neural-Rendering-Engine](https://github.com/Custardtart77/Neural-Rendering-Engine).
- GitHub, [Nyx](https://github.com/moonlovelj/Nyx).
