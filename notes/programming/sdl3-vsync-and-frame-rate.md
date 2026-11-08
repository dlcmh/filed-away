# VSync and frame-rate targets in SDL3

> Based on a DeepSeek conversation about VSync and 120 FPS game loops: [shared conversation](https://chat.deepseek.com/share/lnhtg28zuz362apm4d).

VSync synchronizes presentation with the display refresh. It does not guarantee that the game loop, simulation, or rendering work will run at an exact frame rate.

On a 120 Hz display, the frame budget is:

```text
1000 ms / 120 = 8.33 ms
```

If a frame takes longer than 8.33 ms, the loop falls below 120 FPS. If it finishes sooner, VSync waits for the next refresh and throttles the presentation rate. The result is a cap near the refresh rate, not a guarantee that every frame meets it.

## What VSync does

With the SDL renderer API, VSync is enabled with:

```cpp
SDL_SetRenderVSync(renderer, 1);
```

The present call blocks until the display is ready for the next frame. This reduces tearing and limits how often frames are presented.

With the SDL GPU API, presentation is configured through the swapchain rather than `SDL_SetRenderVSync`. The principle is the same: the swapchain's present mode determines whether presentation waits for the display.

VSync does not control how long the game logic takes, how many update steps run, or whether frame times are evenly spaced. It only affects when a completed frame is presented.

## Why VSync alone can look uneven

Operating-system and driver scheduling are not perfectly periodic. Even when the average rate is correct, intervals between frames can vary. That variation is visible as uneven motion or stutter, especially on high-refresh displays.

On macOS with ProMotion displays, VSync alone has been reported to produce uneven pacing. A manual frame cap or a more careful presentation strategy can be smoother in that case.

## Targeting 120 FPS

For SDL3 main callbacks, the application can request an iteration rate:

```cpp
SDL_SetHint(SDL_HINT_MAIN_CALLBACK_RATE, "120");
```

This asks SDL to call `SDL_AppIterate` at 120 Hz. It still does not make the work inside the callback finish within 8.33 ms.

For a traditional loop, calculate the elapsed time and delay until the next target:

```cpp
const Uint64 frame_ns = 1'000'000'000ULL / 120ULL;

Uint64 previous = SDL_GetTicksNS();

while (running) {
    // Process events and update the game.

    const Uint64 now = SDL_GetTicksNS();
    const Uint64 elapsed = now - previous;

    if (elapsed < frame_ns) {
        SDL_DelayPrecise(frame_ns - elapsed);
    }

    previous = SDL_GetTicksNS();
}
```

`SDL_DelayPrecise` waits as closely as the platform allows; ordinary `SDL_Delay` has coarser resolution. The loop should still measure actual elapsed time rather than assume the delay was exact.

## Keep simulation separate from presentation

A frame-rate cap controls presentation frequency. It should not determine the size of a physics or game-logic step. Use a fixed timestep for simulation and render at the display rate, or use a delta time that is clamped to a safe maximum.

Otherwise, a slow frame produces a large update step, and a fast frame produces a tiny one. The behavior of the game changes with rendering performance.

## Summary

- VSync caps presentation near the refresh rate; it does not guarantee an exact 120 FPS.
- A 120 Hz display gives each frame an 8.33 ms budget.
- VSync alone can produce uneven frame pacing.
- SDL3 main callbacks can request 120 Hz with `SDL_HINT_MAIN_CALLBACK_RATE`.
- Manual loops need elapsed-time measurement and a precise delay for a stable cap.
- Keep simulation timestep independent of the presentation rate.

## Reference

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/lnhtg28zuz362apm4d).
