# SDL_WINDOW_METAL is a capability hint, not Metal initialization

> Why a window created with `SDL_WINDOW_METAL` remains blank until `SDL_Metal_CreateView` attaches a Metal view.

`SDL_WINDOW_METAL` requests a native window that can host a Metal drawable. It is not an instruction to initialize Metal, and it does not create any Metal objects.

## What the flag does

```cpp
SDL_Window* window = SDL_CreateWindow(
    "Metal window", 1280, 720, SDL_WINDOW_METAL | SDL_WINDOW_RESIZABLE);
```

On macOS, this still creates an ordinary `NSWindow` backed by Cocoa. The flag tells SDL that the window may later host a Metal view. It does not create:

- an `MTLDevice`;
- a command queue;
- a `CAMetalLayer`;
- a render pipeline;
- a renderer.

Those objects belong to the application and are created after window initialization.

The flag also affects platform validation: on a platform without Metal support, `SDL_CreateWindow` fails when `SDL_WINDOW_METAL` is set. macOS supports Metal, so creation succeeds.

## What creates the Metal surface

The Metal surface appears when the application calls:

```cpp
SDL_MetalView view = SDL_Metal_CreateView(window);
```

SDL creates a `CAMetalLayer`-backed `NSView` and attaches it to the window. Metal-cpp then creates the `MTLDevice`, command queue, and pipeline state, obtains drawables from the layer, and begins submitting drawing commands.

| Stage | Result |
| --- | --- |
| `SDL_CreateWindow(..., SDL_WINDOW_METAL)` | Native `NSWindow` prepared for a Metal view; no Metal objects |
| `SDL_Metal_CreateView(window)` | `CAMetalLayer`-backed `NSView` attached to the window |
| metal-cpp device and pipeline setup | `MTLDevice`, queue, pipeline state, and drawables |

## Why the window is blank

The blank window is the expected intermediate state: the native window exists, but no Metal drawable or pipeline has been attached, so there is nothing to present. This is not a failure of `SDL_CreateWindow`.

Omitting the flag would produce a window that was not explicitly prepared for a Metal view. Setting it at creation avoids destroying and recreating the window when the Metal view is attached.

The next step is to attach the Metal view and clear it to a solid color.
