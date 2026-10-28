# Using SDL3 on macOS without Metal-cpp

> Based on a DeepSeek conversation about launching a macOS game window with SDL3: [shared conversation](https://chat.deepseek.com/share/5i7iyzotm0al7cly01).

SDL3 is sufficient to create a game window and render with the GPU on macOS. Application code does not need to call Cocoa or Metal directly. SDL3 creates the native window and, when the GPU API is used, selects Metal as the backend.

## What SDL3 handles

A normal SDL3 program calls `SDL_CreateWindow` after initializing the video subsystem. SDL3 creates and manages the macOS window internally. Cocoa and Metal are implementation details inside SDL, not requirements for the application.

For hardware-accelerated rendering, use the SDL3 GPU API rather than the older renderer API. The GPU API maps to Metal on macOS and avoids writing Objective-C or Metal-cpp.

## Minimal GPU clear example

The following program creates a window, initializes a GPU device, claims the window for GPU rendering, and clears the screen to blue each frame.

```cpp
#include <SDL3/SDL.h>

int main() {
    if (!SDL_Init(SDL_INIT_VIDEO)) {
        SDL_Log("SDL_Init failed: %s", SDL_GetError());
        return 1;
    }

    SDL_Window* window = SDL_CreateWindow("SDL3 GPU Clear", 800, 600, 0);
    if (!window) {
        SDL_Log("SDL_CreateWindow failed: %s", SDL_GetError());
        SDL_Quit();
        return 1;
    }

    SDL_ShowWindow(window);

    SDL_GPUDevice* device =
        SDL_CreateGPUDevice(SDL_GPU_SHADERFORMAT_MSL, false, nullptr);

    if (!device) {
        SDL_Log("SDL_CreateGPUDevice failed: %s", SDL_GetError());
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }

    if (!SDL_ClaimWindowForGPUDevice(device, window)) {
        SDL_Log("SDL_ClaimWindowForGPUDevice failed: %s", SDL_GetError());
        SDL_DestroyGPUDevice(device);
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }

    bool running = true;
    SDL_Event event;

    while (running) {
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_EVENT_QUIT) {
                running = false;
            }
        }

        SDL_GPUCommandBuffer* command =
            SDL_AcquireGPUCommandBuffer(device);

        SDL_GPUTexture* swapchain = nullptr;

        if (SDL_WaitAndAcquireGPUSwapchainTexture(
                command, window, &swapchain, nullptr, nullptr)) {
            SDL_GPUColorTargetInfo target{};
            target.texture = swapchain;
            target.clear_color = SDL_FColor{0.0f, 0.0f, 1.0f, 1.0f};
            target.load_op = SDL_GPU_LOADOP_CLEAR;
            target.store_op = SDL_GPU_STOREOP_STORE;

            SDL_GPURenderPass* pass =
                SDL_BeginGPURenderPass(command, &target, 1, nullptr);

            SDL_EndGPURenderPass(pass);
        }

        SDL_SubmitGPUCommandBuffer(command);
    }

    SDL_ReleaseWindowFromGPUDevice(device, window);
    SDL_DestroyGPUDevice(device);
    SDL_DestroyWindow(window);
    SDL_Quit();
    return 0;
}
```

This example only clears the screen; it does not draw geometry. A real program should check every SDL call and handle the path where no swapchain texture is acquired. The structure is still useful: device, claim, command buffer, swapchain, render pass, submit.

## The important calls

- `SDL_CreateWindow` takes a title, width, height, and flags. In SDL3 it takes four arguments, not the six used by SDL2.
- `SDL_ShowWindow` is required in SDL3 because new windows are created hidden.
- `SDL_CreateGPUDevice` selects the shader formats the application can supply. On macOS, `SDL_GPU_SHADERFORMAT_MSL` selects Metal Shading Language.
- `SDL_ClaimWindowForGPUDevice` associates the native window with the GPU device and creates the swapchain.
- `SDL_WaitAndAcquireGPUSwapchainTexture` obtains the next drawable texture.
- A render pass with `SDL_GPU_LOADOP_CLEAR` and `clear_color` performs the clear. No shader is required for a clear-only pass.
- `SDL_SubmitGPUCommandBuffer` submits the work.
- Cleanup releases the window from the device before destroying the device and window.

## Is Metal-cpp required?

No, not when using the SDL3 GPU API normally. SDL3 owns the Metal device, command buffers, textures, and synchronization.

Metal-cpp or direct Metal is relevant only when the program needs something outside SDL's GPU abstraction, such as:

- attaching native Metal rendering to an SDL window with `SDL_Metal_CreateView`;
- retrieving SDL's internal Metal command encoder with `SDL_GetRenderMetalCommandEncoder`;
- implementing custom Metal objects or passes that SDL does not expose.

When compiling SDL3 from source, keep `SDL_METAL=ON`. Older SDL3 versions had a configuration bug where disabling Vulkan could leave the Metal backend out, causing GPU initialization to fail.

## Why the SDL API looks like C

SDL is written in C so it can be called from C, C++, Rust, Python, and other languages. C has no namespaces, so public names carry an `SDL_` prefix. Constants and flags are often macros, which by convention use uppercase names. Apple's C-based frameworks follow the same pattern.

![Screenshot of SDL C API code from the conversation](images/sdl-c-api-style.webp)

*The screenshot from the conversation shows C-style SDL code. It mixes SDL2 and SDL3 calls, so it is illustrative of the naming style, not a compilable SDL3 example.*

A thin C++ wrapper can hide the C surface without replacing SDL:

```cpp
#include <memory>

struct WindowDeleter {
    void operator()(SDL_Window* window) const {
        SDL_DestroyWindow(window);
    }
};

using Window = std::unique_ptr<SDL_Window, WindowDeleter>;

Window create_window(const char* title, int width, int height) {
    return Window(SDL_CreateWindow(title, width, height, 0));
}
```

For a window claimed by a GPU device, release it from the device before the deleter destroys it. The wrapper manages the window lifetime; it does not replace the GPU cleanup sequence.

## Build notes

With Homebrew SDL3 and CMake:

```cmake
find_package(SDL3 CONFIG REQUIRED)
target_link_libraries(game PRIVATE SDL3::SDL3)
```

For custom shaders, provide Metal Shading Language on macOS. SDL_shadercross can translate HLSL or SPIR-V when needed.

## Summary

SDL3 is enough for a macOS window and GPU clear. The application can stay in C++ and avoid Metal-cpp unless it needs direct access to native Metal objects. Use the four-argument SDL3 window API, show the window explicitly, claim it for the GPU device, clear through a render pass, and release it before destroying the device.
