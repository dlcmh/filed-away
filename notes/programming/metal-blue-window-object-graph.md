# How a blue background reaches the screen in Metal

> A beginner's walkthrough of [`src/apps/darkbluewindow/main.cpp`](https://github.com/dlcmh/cppgamearch/blob/main/src/apps/darkbluewindow/main.cpp). The program performs a sequence of explicit steps because three systems participate in one frame: the window system, the GPU API, and the display compositor.

Rendering a single color still requires a chain of objects. Each object answers a different question: where the window is, which GPU is used, which image is being written, how commands are submitted, and when the image is presented. This note follows the program in execution order and explains the role of each stage.

## The mental model

A frame is an image. The application obtains an image from the window's Metal layer, records commands that write into it, submits those commands to the GPU, and presents the image to the display.

The work is split across three layers:

- **Window and platform:** SDL (Simple DirectMedia Layer) creates the native window, pumps events, and exposes a Metal-capable view.
- **GPU submission:** Metal provides the device, command queue, command buffers, encoders, and render passes.
- **Presentation:** Core Animation, macOS's compositing framework, supplies the `CAMetalLayer` and the drawable textures that the display compositor reads.

The compositor combines the application's surface with other windows and sends the result to the display.

The CPU records commands. The GPU executes them asynchronously. The compositor displays the result when the frame is presented.

## Step 1: Create the window

```cpp
SDL_Init(SDL_INIT_VIDEO);
SDL_Window* window = SDL_CreateWindow(
    "darkbluewindow", 1280, 720, SDL_WINDOW_METAL);
```

`SDL_WINDOW_METAL` is a capability flag. It tells SDL that the window may later host a Metal view. It does not create a GPU device or start rendering. On macOS, the result is still an ordinary `NSWindow` managed by Cocoa.

The program uses SDL's event API. It polls events, checks for `SDL_EVENT_QUIT`, and keeps the window alive until the loop ends.

## Step 2: Connect to the GPU

```cpp
MTL::Device* device = MTL::CreateSystemDefaultDevice();
```

`MTL::Device` represents the GPU. It is the factory for textures, buffers, command queues, and pipeline state. The device is independent of the window; the window is a display surface, while the device is the execution resource.

metal-cpp wraps Apple's Objective-C frameworks. Those frameworks use reference counting, and temporary objects such as the string returned by `device->name()` are autoreleased. An `NS::AutoreleasePool` gives those objects a defined cleanup point:

```cpp
NS::AutoreleasePool* pool = NS::AutoreleasePool::alloc()->init();
SDL_Log("Metal device: %s", device->name()->utf8String());
```

The program also creates a smaller pool inside the frame loop, so temporary objects from each frame are released at the end of that frame.

### Why the pool is not passed to later calls

An autorelease pool is not a context object that must be handed to every function that creates temporary objects. It is a per-thread stack. Creating a pool pushes it onto the current thread's stack. When code on that thread sends an object an `autorelease` message, the object is registered with the pool at the top of the stack. Draining the pool pops it and releases the objects registered with it.

The `pool` variable is a handle used to drain that stack entry. It does not need to travel with calls such as `SDL_Metal_CreateView`, `layer->nextDrawable()`, or `commandQueue->commandBuffer()`. Those calls run on the same thread, so any autoreleased temporaries they create join the current top pool automatically.

Nested pools follow the same stack rule. The per-frame pool becomes the top pool for the duration of an iteration. When it drains, the outer pool becomes the top again, and later autoreleased objects are registered there.

The rule is thread-specific. A pool created on the main thread does not collect autoreleased objects created on a worker thread. Code that creates Cocoa objects on another thread must establish a pool on that thread, or use an API that provides one.

## Step 3: Give the window a Metal surface

A window alone cannot receive GPU output. The application needs a Metal layer attached to the window:

```cpp
SDL_MetalView view = SDL_Metal_CreateView(window);
CA::MetalLayer* layer =
    static_cast<CA::MetalLayer*>(SDL_Metal_GetLayer(view));

layer->setDevice(device);
layer->setPixelFormat(MTL::PixelFormatBGRA8Unorm);
```

`SDL_Metal_CreateView` creates an `NSView` backed by a `CAMetalLayer` and installs it in the window. `SDL_Metal_GetLayer` returns the layer as an opaque pointer, which the program casts to `CA::MetalLayer`.

The layer is the bridge between the operating system's compositor and the GPU. It owns a small set of drawable textures, often called a swapchain. A drawable is one frame-sized image that the layer can make available to the compositor. Each frame, the application requests one of those images, writes into it, and presents it.

Two configuration calls complete the association:

- `setDevice(device)` tells the layer which GPU produces its images. SDL deliberately leaves this association to the application.
- `setPixelFormat(MTL::PixelFormatBGRA8Unorm)` chooses the byte layout of the drawable textures. The format describes memory storage; shader code still uses logical RGBA components. See [Why BGRA8Unorm does not mean BGR colors in a Metal shader](metal-bgra8unorm-color-order.md) for the distinction.

The layer is owned by the view. The application configures it but does not release it.

## Step 4: Prepare the submission machinery

Two long-lived objects are created before the loop:

```cpp
MTL::CommandQueue* commandQueue = device->newCommandQueue();

MTL::RenderPassDescriptor* pass = MTL::RenderPassDescriptor::alloc()->init();
MTL::RenderPassColorAttachmentDescriptor* color =
    pass->colorAttachments()->object(0);

color->setLoadAction(MTL::LoadActionClear);
color->setStoreAction(MTL::StoreActionStore);
color->setClearColor(MTL::ClearColor::Make(0.05, 0.05, 0.12, 1.0));
```

The command queue is the channel through which command buffers reach the GPU. It is created once because it is a long-lived submission resource.

The render pass descriptor is a recipe, not GPU work. An attachment is a texture that the pass reads or writes; this pass has one color attachment. The descriptor states:

- which texture is the color attachment;
- what happens when the pass begins (`LoadActionClear`);
- what happens when the pass ends (`StoreActionStore`);
- which color is used for the clear.

The descriptor is created once. Each frame, the program replaces its texture with the current drawable's texture.

## Step 5: Record and submit one frame

The frame loop performs the core sequence:

```cpp
while (running) {
    NS::AutoreleasePool* framePool = NS::AutoreleasePool::alloc()->init();

    // ... poll events ...

    CA::MetalDrawable* drawable = layer->nextDrawable();
    if (drawable) {
        color->setTexture(drawable->texture());

        MTL::CommandBuffer* commandBuffer = commandQueue->commandBuffer();
        MTL::RenderCommandEncoder* encoder =
            commandBuffer->renderCommandEncoder(pass);

        encoder->endEncoding();

        commandBuffer->presentDrawable(drawable);
        commandBuffer->commit();
    }

    framePool->drain();
}
```

The frame pool is created at the top of each iteration and drained at the end. None of the calls inside the iteration receives it as an argument.

The sequence has five conceptual steps:

1. **Acquire an image.** `nextDrawable()` returns a drawable, which contains a texture. A texture is GPU memory holding pixels; the drawable pairs that texture with presentation metadata. The layer may wait if too many frames are still in flight.
2. **Bind the target.** `color->setTexture(...)` makes that texture the color attachment of the render pass.
3. **Record commands.** A command buffer is created from the queue. A render command encoder begins the pass. The clear load action writes the dark blue color into the texture.
4. **Close the pass.** `endEncoding()` finishes the encoder. No draw calls are recorded; the clear and store actions are the entire pass.
5. **Present and submit.** `presentDrawable(drawable)` schedules the image for display, and `commit()` submits the command buffer to the GPU.

The CPU then continues. The GPU executes the command buffer asynchronously, and the compositor displays the drawable when the work completes.

## Step 6: Release resources

metal-cpp objects are reference counted. The program explicitly releases the pass, queue, view, device, window, and autorelease pool:

```cpp
pass->release();
commandQueue->release();
SDL_Metal_DestroyView(view);
device->release();
SDL_DestroyWindow(window);
SDL_Quit();
pool->drain();
```

The order reflects ownership: the pass and queue are released before the device that created them, the view is destroyed before the window, and the pool is drained after the objects that may have created autoreleased temporaries.

## Clear is not draw

The blue background is produced by a clear, not by a draw call. The render pass begins with `LoadActionClear`, which writes the clear color into the drawable texture. The encoder contains no pipeline state, vertex data, or fragment shader.

A render pipeline is the configured GPU program and state used by draw calls: the vertex and fragment shader stages, blending rules, and attachment formats. A clear does not need a pipeline because it does not process geometry. Adding a triangle or a sprite would require a pipeline object, a vertex buffer, and a draw call inside the encoder, while reusing the same device, queue, layer, drawable, pass, and command buffer.

## The objects as questions

| Object | Question it answers |
| --- | --- |
| `SDL_Window` | Where is the operating-system window? |
| `MTL::Device` | Which GPU is used? |
| `NS::AutoreleasePool` | Which per-thread pool collects Cocoa temporaries? |
| `SDL_MetalView` | Which native view hosts the Metal surface? |
| `CA::MetalLayer` | Which layer supplies images to the compositor? |
| `MTL::CommandQueue` | Where are command buffers submitted? |
| `MTL::RenderPassDescriptor` | Which images are written, and how are they loaded and stored? |
| `CA::MetalDrawable` | Which image belongs to this frame? |
| `MTL::CommandBuffer` | What work belongs to this submission? |
| `MTL::RenderCommandEncoder` | Which render pass is currently being recorded? |

## What to remember

- A frame is an image obtained from the layer, filled by GPU commands, and presented to the display.
- The layer is the bridge between the window system and the GPU.
- A command queue accepts command buffers; a command buffer records work; an encoder records one pass.
- A render pass descriptor defines the target texture and the load/store behavior.
- A clear writes a color without drawing geometry.
- Autorelease pools are per-thread stacks; code on the same thread uses the current pool without receiving it as an argument.
- Owned metal-cpp objects require explicit release; autorelease pools manage Cocoa temporaries.

The next steps in the application are a render pipeline, shaders, vertex data, and draw calls. Those stages fit inside the same frame structure.

## Reference

- Source file: [`darkbluewindow/main.cpp`](https://github.com/dlcmh/cppgamearch/blob/main/src/apps/darkbluewindow/main.cpp).
