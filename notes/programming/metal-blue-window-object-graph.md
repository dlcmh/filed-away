# Why a blue Metal window requires so many objects

> An architecture note on [`src/apps/darkbluewindow/main.cpp`](https://github.com/dlcmh/cppgamearch/blob/main/src/apps/darkbluewindow/main.cpp). The program clears a window to dark blue; the object graph is larger than the visual result because it exercises the explicit Metal swapchain path.

The code can look disproportionate: a window, a view, a layer, a GPU device, a command queue, a render pass, a drawable, a command buffer, an encoder, and an autorelease pool, all to produce a blue rectangle. The objects are not arbitrary. Each one has a distinct owner, lifetime, and responsibility, and the handoffs occur at the boundaries between SDL, Core Animation, Metal, and Cocoa.

## The program clears; it does not draw

The blue background is produced by a render pass with a clear load action:

```cpp
color->setLoadAction(MTL::LoadActionClear);
color->setStoreAction(MTL::StoreActionStore);
color->setClearColor(MTL::ClearColor::Make(0.05, 0.05, 0.12, 1.0));
```

The render command encoder contains no draw calls and no pipeline state. It begins the pass, which clears the drawable texture, and ends the pass, which stores the result. The program is therefore a test of the presentation path, not of a shader or a mesh. That is why the object graph is mostly initialization and submission machinery rather than rendering logic.

## The object graph

```text
SDL_Window
  └─ SDL_Metal_CreateView
       └─ SDL_MetalView
            └─ SDL_Metal_GetLayer
                 └─ CA::MetalLayer
                      ├─ setDevice(MTL::Device)
                      └─ nextDrawable
                           └─ CA::MetalDrawable
                                └─ texture()
                                     └─ render pass color attachment

MTL::Device
  └─ MTL::CommandQueue
       └─ MTL::CommandBuffer
            └─ MTL::RenderCommandEncoder(render pass)
                 └─ endEncoding
                      └─ presentDrawable
                           └─ commit
```

| Object | Created by | Lifetime | Responsibility |
| --- | --- | --- | --- |
| `SDL_Window` | SDL | Until `SDL_DestroyWindow` | Native window, event loop, platform surface |
| `MTL::Device` | `MTL::CreateSystemDefaultDevice` | Application-owned until release | GPU connection and resource factory |
| `NS::AutoreleasePool` | `alloc()->init()` | Until `drain()` | Cocoa/metal-cpp temporary object cleanup |
| `SDL_MetalView` | `SDL_Metal_CreateView` | Until `SDL_Metal_DestroyView` | Cocoa view that hosts the Metal layer |
| `CA::MetalLayer` | SDL, retrieved as a borrowed pointer | Owned by the view | Drawable provider and pixel-format configuration |
| `MTL::CommandQueue` | `newCommandQueue` | Application-owned until release | Serial submission of command buffers |
| `MTL::RenderPassDescriptor` | `alloc()->init()` | Application-owned until release | Render target attachments, clear/store behavior |
| `CA::MetalDrawable` | `layer->nextDrawable()` | Per frame, through presentation | Texture that represents the current frame |
| `MTL::CommandBuffer` | `commandQueue->commandBuffer()` | Per frame, through completion | Recorded GPU commands |
| `MTL::RenderCommandEncoder` | `commandBuffer->renderCommandEncoder(pass)` | Per frame, until `endEncoding` | Encodes the render pass |

The per-frame handoff is compact:

```cpp
CA::MetalDrawable* drawable = layer->nextDrawable();
if (drawable) {
    color->setTexture(drawable->texture());
    MTL::CommandBuffer* commandBuffer = commandQueue->commandBuffer();
    MTL::RenderCommandEncoder* encoder = commandBuffer->renderCommandEncoder(pass);
    encoder->endEncoding();
    commandBuffer->presentDrawable(drawable);
    commandBuffer->commit();
}
```

The brevity is deceptive: each call binds a resource or transfers a frame into the submission path.

The layer is a borrowed pointer from SDL; the application configures it but does not own it. The device, queue, and pass descriptor are long-lived application objects. The drawable, command buffer, and encoder are per-frame objects. The per-frame autorelease pool covers the temporary Cocoa objects created during that frame.

## Why each handoff exists

### SDL window to Metal view

SDL owns the window and the platform event loop. `SDL_WINDOW_METAL` only marks the window as capable of hosting a Metal view; it does not initialize Metal. `SDL_Metal_CreateView` performs the Cocoa-specific work of creating an `NSView` backed by a `CAMetalLayer` and installing it in the window.

### Metal view to `CA::MetalLayer`

SDL exposes the layer as an opaque pointer. The application casts it to `CA::MetalLayer`, sets the `MTL::Device`, and chooses the pixel format. SDL deliberately does not own the device or the renderer, so this association remains the application's responsibility.

### Device to command queue

The `MTL::Device` creates resources and the `MTL::CommandQueue`. The queue is created once because command buffers are submitted through a long-lived queue; creating a queue per frame would add overhead without changing the result.

### Layer to drawable

The layer is the source of drawables. `nextDrawable()` returns the texture for the current frame. The render pass descriptor replaces its previous color texture with the new drawable's texture, and the encoder clears that texture.

### Command buffer to encoder to presentation

The command buffer records the work, the render command encoder records the pass, and `presentDrawable` associates the finished texture with the layer's presentation path. `commit` submits the buffer to the queue. This sequence is the explicit Metal model: the application states what is rendered, where it is stored, and when it is presented.

### Autorelease pool

metal-cpp wraps Objective-C objects in C++ classes that follow Cocoa's reference-counting conventions. Temporary objects such as the device name string and internal Foundation objects are autoreleased. The pool gives those objects a defined cleanup point, and the per-frame pool prevents temporary objects from accumulating across frames.

## Is the complexity justified?

The answer depends on the purpose of the program.

**As a learning scaffold, yes.** The repository is being built step by step: first a window, then a Metal-capable window, then a cleared window. Each stage exposes one layer of the platform stack. Keeping the objects visible makes the Metal submission model observable; hiding them behind a helper would remove the lesson.

**As the minimum for a reusable Metal renderer, yes.** A device, queue, layer, pass descriptor, drawable, command buffer, and encoder are the minimum explicit objects needed to present a frame. Once a pipeline and draw calls are added, they reuse the same objects. The blue clear is the smallest vertical slice through the full path.

**As the minimum for a blue window, no.** If the only requirement were a blue rectangle with no Metal-specific work, `SDL_Renderer` would be shorter, and an `MTKView` with a clear color would avoid most of the explicit Metal setup. The explicit path is justified by the intention to build a custom engine, not by the visual result.

## Where the sample is over-explicit

The object graph is justified, but `main.cpp` is still a demonstration rather than a finished architecture:

- Cleanup is repeated on every error path. A small RAII wrapper for the device, queue, pass, view, and autorelease pool would remove the duplication without hiding the Metal sequence.
- The render pass descriptor is created once and its texture is replaced each frame. That is acceptable for a single in-flight frame, but a renderer with multiple frames in flight should use per-frame descriptors or otherwise ensure that no descriptor is mutated while an earlier frame is still being encoded or executed.
- The loop commits command buffers without explicit frame pacing or a completion wait. The layer's drawable availability provides some backpressure, but a production renderer needs a defined policy for frames in flight and shutdown.
- Resize handling and drawable-size changes are absent. A renderer that presents continuously must recreate size-dependent state when the window changes.

None of these points invalidates the object graph. They identify what remains to be encapsulated as the sample grows into an engine.

## Summary

The apparent gymnastics are the explicit ownership and submission model of Metal combined with SDL's division of responsibility. SDL owns the window and view; the application owns the device, queue, pass, and frame encoding; Core Animation supplies the layer and drawables; Foundation supplies the autorelease pool. A blue background requires clearing a drawable, and clearing a drawable requires the swapchain and command-submission path.

The complexity is justified as a learning scaffold and as the foundation of a custom renderer. It would be unnecessary if the goal were only a blue window.
