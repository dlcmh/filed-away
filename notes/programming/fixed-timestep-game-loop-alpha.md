# What alpha means in a fixed-timestep game loop

> Based on a DeepSeek conversation about clean C++ game loops at 60 Hz and 120 Hz: [shared conversation](https://chat.deepseek.com/share/9vmyfcg7hdlkl78ibs). In that discussion, **alpha** is the render interpolation factor, not the alpha channel used for transparency.

A fixed-timestep loop separates simulation from rendering. The simulation advances in equal steps, while rendering runs at the display's rate. The accumulator stores time that has arrived but has not yet been consumed by a simulation step. Alpha is the fraction of a simulation step left in that accumulator.

## The accumulator

```cpp
accumulator += frameTime;

while (accumulator >= fixedDt) {
    update(fixedDt);
    accumulator -= fixedDt;
}
```

If `fixedDt` is `1.0 / 60.0`, each iteration of the inner loop advances the game by one sixtieth of a second. After the loop, `accumulator` is smaller than `fixedDt`; it is the time remaining until the next simulated tick.

```cpp
double alpha = accumulator / fixedDt;
```

Because the inner loop runs while `accumulator >= fixedDt`, alpha falls in the range `[0, 1)`. An alpha of `0` means the render occurs exactly at a simulation boundary. An alpha near `1` means the render occurs almost one full tick after the last simulation state.

## Why interpolation is needed

The simulation state changes only at fixed intervals. If the display refreshes between those intervals, rendering the current state directly produces motion that advances in visible steps. At 60 Hz simulation and 120 Hz display, every simulation step spans two display frames; one of those frames has no new simulation state.

Interpolation uses the previous and current simulation states to produce a position between them:

```cpp
State previous = current;

while (running) {
    const double frameTime = std::clamp(now() - lastTime, 0.0, 0.25);
    lastTime = now();
    accumulator += frameTime;

    while (accumulator >= fixedDt) {
        previous = current;
        update(current, fixedDt);
        accumulator -= fixedDt;
    }

    const double alpha = accumulator / fixedDt;
    render(previous, current, alpha);
}
```

The renderer computes an interpolated value:

```cpp
const Vec3 renderPosition =
    lerp(previous.position, current.position, alpha);
```

At `alpha = 0`, the rendered position is the previous state; at `alpha` approaching `1`, it approaches the current state. The renderer is therefore one simulation interval behind the newest state, but the displayed motion is continuous rather than stepped.

Alpha by itself is not enough. The loop must retain a previous snapshot of every value that will be interpolated. If only the current state is stored, there is nothing to interpolate from.

## Alpha is not transparency

The name overlaps with the alpha channel in color formats, but the two concepts are unrelated:

- **Color alpha** controls opacity or coverage.
- **Loop alpha** is a normalized fraction of elapsed simulation time.

The same word is used because both act as interpolation parameters. In a game loop, alpha is the `t` in `lerp(a, b, t)`.

## 60 Hz and 120 Hz

The simulation rate and the render rate are independent:

- A **60 Hz simulation** with a **60 Hz display** still benefits from interpolation because frame arrival and simulation ticks are not perfectly aligned.
- A **60 Hz simulation** with a **120 Hz display** renders two frames per simulation step. Alpha moves between the two simulation states across those frames.
- A **120 Hz simulation** with a **120 Hz display** reduces the distance between states and the amount of interpolation, at the cost of more simulation work.
- A **120 Hz simulation** with a **60 Hz display** performs two updates per rendered frame; the renderer sees the latest state and alpha near the end of the interval.

The fixed step should be chosen from the simulation's requirements, not from the monitor's refresh rate. Higher simulation rates can make collision and motion more accurate, but they also increase CPU cost.

## Practical cautions

- **Clamp long frames.** The `0.25` second clamp prevents a stalled frame from triggering an unbounded number of catch-up updates, the spiral of death. Clamping discards time, so the simulation temporarily runs slower than wall-clock time.
- **Process input per update.** Handling input once per rendered frame while simulating at a different rate can make behavior depend on display refresh. Input sampled per fixed update keeps the simulation consistent.
- **Snapshot cost.** Retaining previous state costs memory and copying. Interpolate only the values that affect rendering; simulation-only state does not need a snapshot.
- **Do not confuse alpha with a time delta.** Alpha is dimensionless and falls between 0 and 1. Converting it to seconds requires multiplying by `fixedDt`.

## Summary

Alpha is the fraction of a fixed simulation step remaining after the update loop consumes whole steps. The renderer uses it to interpolate between the previous and current states, producing smooth motion when rendering and simulation run at different rates. It is an interpolation parameter, not a transparency value.

## References

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/9vmyfcg7hdlkl78ibs).
- Game Programming Patterns, [Game Loop](https://gameprogrammingpatterns.com/game-loop.html).
