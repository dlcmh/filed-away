# What `1000ULL` means in an FPS counter

> Based on a DeepSeek conversation about the `1000ULL` comparison in a frame-rate counter: [shared conversation](https://chat.deepseek.com/share/zs82d1irdsbxpg19bw).

```cpp
Uint64 lastFpsTick = SDL_GetTicks();
int framesThisSecond = 0;

while (running) {
    ++framesThisSecond;

    const Uint64 now = SDL_GetTicks();
    if (now - lastFpsTick >= 1000ULL) {
        SDL_Log("FPS: %d", framesThisSecond);
        framesThisSecond = 0;
        lastFpsTick = now;
    }
}
```

`1000ULL` is an integer literal with two suffixes:

- `U` means **unsigned**.
- `LL` means **long long**.

Together, `ULL` means **unsigned long long**. The literal has the value 1000 and the type `unsigned long long`, which is at least 64 bits wide.

It is not a special SDL type or a time unit. It is the number 1000 written with a type that matches the unsigned 64-bit arithmetic around it.

## Why the suffix is used

`SDL_GetTicks()` returns `Uint64`, an unsigned 64-bit tick count in milliseconds. Therefore:

```cpp
now - lastFpsTick
```

is an unsigned 64-bit value. Comparing it with `1000ULL` keeps both sides unsigned and 64-bit:

```cpp
if (now - lastFpsTick >= 1000ULL) {
```

A plain `1000` would normally work because the comparison would convert it to the unsigned type. The explicit suffix avoids sign/width mismatch warnings, particularly with strict warning flags such as `-Wsign-compare` or `-Wconversion`. It also documents that the comparison is against the same kind of quantity as the tick count.

## What the block does

The counter measures frames per second:

1. Increment `framesThisSecond` for the current frame.
2. Read the current tick count.
3. If at least 1000 milliseconds have elapsed since the last sample, log the frame count.
4. Reset the frame count and record the new sample time.

`SDL_GetTicks()` returns milliseconds, so `1000ULL` means one second. It is not the type of a duration; it is the numeric threshold.

## Related suffixes

| Literal | Type |
| --- | --- |
| `1000` | `int` |
| `1000U` | `unsigned int` |
| `1000L` | `long` |
| `1000UL` | `unsigned long` |
| `1000LL` | `long long` |
| `1000ULL` | `unsigned long long` |

The exact width of `long` and `unsigned long` varies by platform. `unsigned long long` is guaranteed to be at least 64 bits.

## Summary

`1000ULL` is the decimal value 1000 with type `unsigned long long`. In this loop it is the one-second threshold for an unsigned 64-bit millisecond counter. The suffix prevents type-mismatch warnings and makes the intended arithmetic explicit; a plain `1000` would usually produce the same runtime behavior.

## Reference

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/zs82d1irdsbxpg19bw).
