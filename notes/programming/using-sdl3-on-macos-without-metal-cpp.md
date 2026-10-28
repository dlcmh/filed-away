# Using SDL3 on macOS without Metal-cpp

> Based on a DeepSeek conversation about launching a macOS game window with SDL3, with C++ examples from a [follow-up conversation](https://chat.deepseek.com/share/991tqxx1nov5agr63m): [original conversation](https://chat.deepseek.com/share/5i7iyzotm0al7cly01).

SDL3 is sufficient to create a game window and render with the GPU on macOS. Application code does not need to call Cocoa or Metal directly. SDL3 creates the native window and, when the GPU API is used, selects Metal as the backend.

The examples below are C++ programs that call SDL's C API. SDL itself is written in C, but a C++ compiler and C++ syntax can be used throughout.

## Minimal C++ GPU clear

This program creates a window, initializes a GPU device, claims the window for GPU rendering, and clears the screen to teal each frame.

```cpp
#include <SDL3/SDL.h>
#include <SDL3/SDL_gpu.h>

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

    // 0 shader formats is valid for a clear-only program.
    // On macOS, SDL selects the Metal backend automatically.
    // <-- Old code caused: SDL_CreateGPUDevice failed: No supported SDL_GPU backend found! -->
    // SDL_GPUDevice* device = SDL_CreateGPUDevice(0, true, nullptr);

    // The issue stems from an incorrect assumption in your justsdl3 code. While your program only performs a clear operation and doesn't explicitly load any custom shaders, passing 0 as the format_flags parameter is invalid in SDL3.
    // SDL3 chooses its underlying graphics driver (like Metal or Vulkan) by matching the platform's capabilities against the shader formats your application explicitly claims it can provide. By passing 0, you are telling SDL3, "My app supports zero shader formats," which forces the internal selector to conclude that no supported SDL_GPU backend found.
    // The fix: Modify your SDL_CreateGPUDevice call to pass SDL_GPU_SHADERFORMAT_MSL (Metal Shading Language). This signals to SDL3 that your environment intends to interact with the native macOS backend.
    SDL_CreateGPUDevice(SDL_GPU_SHADERFORMAT_MSL, true, nullptr);

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

        SDL_GPUCommandBuffer* command = SDL_AcquireGPUCommandBuffer(device);
        if (!command) {
            SDL_Log("SDL_AcquireGPUCommandBuffer failed: %s", SDL_GetError());
            break;
        }

        SDL_GPUTexture* swapchain = nullptr;

        if (!SDL_WaitAndAcquireGPUSwapchainTexture(
                command, window, &swapchain, nullptr, nullptr)) {
            SDL_Log("SDL_WaitAndAcquireGPUSwapchainTexture failed: %s",
                    SDL_GetError());
            SDL_CancelGPUCommandBuffer(command);
            break;
        }

        if (swapchain) {
            SDL_GPUColorTargetInfo target{};
            target.texture = swapchain;
            target.clear_color = SDL_FColor{0.0f, 0.5f, 0.5f, 1.0f};
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

The clear is performed by the render pass. `SDL_GPU_LOADOP_CLEAR` tells the GPU to overwrite the swapchain texture with `clear_color` before the pass begins. No graphics pipeline or shader is required for this operation.

A null swapchain can occur when the window is minimized. The program still submits the command buffer in that case.

## The important calls

- `SDL_CreateWindow` takes a title, width, height, and flags. SDL3 uses four arguments; the six-argument form belongs to SDL2.
- `SDL_ShowWindow` is required because SDL3 creates windows hidden.
- `SDL_CreateGPUDevice` selects the backend and the shader formats the program can provide. For a clear-only program, `0` is sufficient. When shaders are added, request `SDL_GPU_SHADERFORMAT_MSL` on macOS.
- `SDL_ClaimWindowForGPUDevice` associates the native window with the GPU device and creates the swapchain.
- `SDL_WaitAndAcquireGPUSwapchainTexture` obtains the next drawable texture.
- `SDL_BeginGPURenderPass` with a color target performs the clear; `SDL_EndGPURenderPass` closes it.
- `SDL_SubmitGPUCommandBuffer` submits the work and presents the swapchain texture.
- Cleanup releases the window from the device before destroying the device and window.

## Callback form

SDL3 also supports a callback-based application structure. The GPU work is the same; the while loop and event polling are replaced by `SDL_AppInit`, `SDL_AppEvent`, `SDL_AppIterate`, and `SDL_AppQuit`.

```cpp
#define SDL_MAIN_USE_CALLBACKS 1
#include <SDL3/SDL.h>
#include <SDL3/SDL_main.h>
#include <SDL3/SDL_gpu.h>

struct AppState {
    SDL_Window* window = nullptr;
    SDL_GPUDevice* device = nullptr;
};

SDL_AppResult SDL_AppInit(void** appstate, int, char**) {
    if (!SDL_Init(SDL_INIT_VIDEO)) {
        SDL_Log("SDL_Init failed: %s", SDL_GetError());
        return SDL_APP_FAILURE;
    }

    auto* state = new AppState();
    *appstate = state;

    state->window = SDL_CreateWindow("SDL3 GPU Clear", 800, 600, 0);
    if (!state->window) {
        SDL_Log("SDL_CreateWindow failed: %s", SDL_GetError());
        return SDL_APP_FAILURE;
    }

    SDL_ShowWindow(state->window);

    state->device = SDL_CreateGPUDevice(0, true, nullptr);
    if (!state->device) {
        SDL_Log("SDL_CreateGPUDevice failed: %s", SDL_GetError());
        return SDL_APP_FAILURE;
    }

    if (!SDL_ClaimWindowForGPUDevice(state->device, state->window)) {
        SDL_Log("SDL_ClaimWindowForGPUDevice failed: %s", SDL_GetError());
        return SDL_APP_FAILURE;
    }

    return SDL_APP_CONTINUE;
}

SDL_AppResult SDL_AppEvent(void*, SDL_Event* event) {
    if (event->type == SDL_EVENT_QUIT) {
        return SDL_APP_SUCCESS;
    }
    return SDL_APP_CONTINUE;
}

SDL_AppResult SDL_AppIterate(void* appstate) {
    auto* state = static_cast<AppState*>(appstate);

    SDL_GPUCommandBuffer* command =
        SDL_AcquireGPUCommandBuffer(state->device);
    if (!command) {
        SDL_Log("SDL_AcquireGPUCommandBuffer failed: %s", SDL_GetError());
        return SDL_APP_FAILURE;
    }

    SDL_GPUTexture* swapchain = nullptr;

    if (!SDL_WaitAndAcquireGPUSwapchainTexture(
            command, state->window, &swapchain, nullptr, nullptr)) {
        SDL_Log("SDL_WaitAndAcquireGPUSwapchainTexture failed: %s",
                SDL_GetError());
        SDL_CancelGPUCommandBuffer(command);
        return SDL_APP_FAILURE;
    }

    if (swapchain) {
        SDL_GPUColorTargetInfo target{};
        target.texture = swapchain;
        target.clear_color = SDL_FColor{0.0f, 0.5f, 0.5f, 1.0f};
        target.load_op = SDL_GPU_LOADOP_CLEAR;
        target.store_op = SDL_GPU_STOREOP_STORE;

        SDL_GPURenderPass* pass =
            SDL_BeginGPURenderPass(command, &target, 1, nullptr);

        SDL_EndGPURenderPass(pass);
    }

    SDL_SubmitGPUCommandBuffer(command);
    return SDL_APP_CONTINUE;
}

void SDL_AppQuit(void* appstate, SDL_AppResult) {
    auto* state = static_cast<AppState*>(appstate);

    if (state) {
        if (state->device && state->window) {
            SDL_ReleaseWindowFromGPUDevice(state->device, state->window);
        }
        if (state->device) {
            SDL_DestroyGPUDevice(state->device);
        }
        if (state->window) {
            SDL_DestroyWindow(state->window);
        }
        delete state;
    }

    SDL_Quit();
}
```

The callback form requires `SDL_MAIN_USE_CALLBACKS` before including `SDL_main.h`, and it must not also define `main`. SDL pumps events between `SDL_AppIterate` calls, so no `SDL_PollEvent` loop is needed. The `appstate` pointer carries the window and device between callbacks.

## Is Metal-cpp required?

No, not when using the SDL3 GPU API normally. SDL3 owns the Metal device, command buffers, textures, and synchronization. Metal-cpp or direct Metal is relevant only when the program needs something outside SDL's GPU abstraction, such as:

- attaching native Metal rendering to an SDL window with `SDL_Metal_CreateView`;
- retrieving SDL's internal Metal command encoder with `SDL_GetRenderMetalCommandEncoder`;
- implementing custom Metal objects or passes that SDL does not expose.

When compiling SDL3 from source, keep `SDL_METAL=ON`. Older SDL3 versions had a configuration bug where disabling Vulkan could leave the Metal backend out, causing GPU initialization to fail.

## Why the SDL API looks like C

SDL is written in C so it can be called from C, C++, Rust, Python, and many other languages. C has no namespaces, so public names carry an `SDL_` prefix. Constants and flags are often macros, which by convention use uppercase names. Apple's C-based frameworks follow the same pattern.

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

For a window claimed by a GPU device, release it from the device before the deleter destroys it. The wrapper manages the window lifetime; it does not replace the GPU cleanup sequence. The full examples above keep the GPU cleanup explicit for that reason.

## Build notes

With Homebrew SDL3 and CMake:

```cmake
find_package(SDL3 CONFIG REQUIRED)
target_link_libraries(game PRIVATE SDL3::SDL3)
```

For custom shaders, provide Metal Shading Language on macOS. SDL_shadercross can translate HLSL or SPIR-V when needed.

## Summary

SDL3 is enough for a macOS window and GPU clear. The application can stay in C++ and avoid Metal-cpp unless it needs direct access to native Metal objects. Use the four-argument SDL3 window API, show the window explicitly, claim it for the GPU device, clear through a render pass, and release it before destroying the device. Both the explicit loop and the callback form use the same GPU calls.
