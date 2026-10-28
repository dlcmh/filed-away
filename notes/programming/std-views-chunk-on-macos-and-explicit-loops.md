# std::views::chunk on macOS, and when explicit loops are better

> Based on a DeepSeek conversation about chunking, filtered views, and explicit game loops: [shared conversation](https://chat.deepseek.com/share/5i7iyzotm0al7cly01).

`std::views::chunk` is a C++23 range adaptor that divides a range into consecutive subranges of a fixed size. It is useful for processing data in batches:

```cpp
for (auto batch : values | std::views::chunk(4)) {
    process(batch);
}
```

On macOS with Apple Clang, this code may not compile even with `-std=c++23`, because the standard library has not implemented the feature.

## Why chunk is missing

`std::views::chunk` is a library feature, not only a language feature. It comes from proposal P2442R1 and is exposed when the standard library defines `__cpp_lib_ranges_chunk`.

A compiler can accept C++23 syntax while its bundled library lacks a C++23 facility. At the time of writing, Apple's libc++ does not provide `views::chunk`, so the example above fails with an error such as:

```text
no member named 'chunk' in namespace 'std::ranges::views'
```

`std::views::chunk_by` is a different adaptor: it groups elements according to a predicate. It does not provide fixed-size chunks.

The feature-test macro makes the limitation explicit:

```cpp
#if defined(__cpp_lib_ranges_chunk)
// chunk-based implementation
#else
// fallback
#endif
```

## Replacing chunk with an index loop

For a contiguous container such as `std::vector`, an explicit index loop is the simplest fallback:

```cpp
#include <algorithm>
#include <cstddef>
#include <vector>

struct Enemy {
    float x = 0.0f;
    float y = 0.0f;
    bool alive = true;
};

void update(std::vector<Enemy>& enemies) {
    constexpr std::size_t batch_size = 4;

    for (std::size_t base = 0; base < enemies.size(); base += batch_size) {
        const std::size_t end =
            std::min(base + batch_size, enemies.size());

        for (std::size_t i = base; i < end; ++i) {
            Enemy& enemy = enemies[i];

            if (!enemy.alive) {
                continue;
            }
            if (enemy.x <= 0.0f || enemy.x >= 800.0f) {
                continue;
            }

            // Update the enemy.
            enemy.x += 1.0f;
        }
    }
}
```

`std::min` handles the final, partially filled batch. The code operates directly on the vector's storage and introduces no view objects.

If batching is unnecessary, the plain loop is even simpler:

```cpp
for (Enemy& enemy : enemies) {
    if (!enemy.alive) {
        continue;
    }
    if (enemy.x <= 0.0f || enemy.x >= 800.0f) {
        continue;
    }

    enemy.x += 1.0f;
}
```

## What chunk does not do

A chunk view groups the elements of an existing view. It does not copy them into a new contiguous buffer.

This matters when a filter comes first:

```cpp
auto visible = enemies
    | std::views::filter([](const Enemy& e) { return e.alive; })
    | std::views::filter([](const Enemy& e) { return e.x > 0.0f && e.x < 800.0f; });

for (auto batch : visible | std::views::chunk(4)) {
    // batch is a view over selected elements, not a contiguous copy
}
```

The selected enemies may be scattered throughout the original vector. Chunking that filtered view does not make them adjacent in memory, so it does not by itself provide cache locality or enable SIMD over four contiguous objects.

If contiguous batches are required, collect indices or pointers into a separate vector, or process contiguous ranges of the original storage and skip unwanted elements inside the loop.

## Are filtered views slower?

They can be, but not always. A `filter_view` is lazy: each iteration applies the predicate and advances the underlying iterator. When the predicate is trivial and the compiler inlines the whole pipeline, the result can be as fast as a hand-written loop. When inlining is incomplete, the iterator and predicate layers can add measurable overhead.

Benchmarks have shown cases where range pipelines execute more instructions than a direct loop, and the gap depends on the compiler, optimization level, predicate, and element type. It is not accurate to describe ranges as universally zero-cost or universally slow.

`filter_view` also has some stateful behavior: its `begin()` caches the first matching iterator, while `end()` is not cached. For a vector the end check is cheap, but the abstraction can make optimization harder in a hot loop.

The practical rule is:

- use a range pipeline when it makes a non-critical section clearer;
- use an explicit loop in a measured hot path when the compiler does not optimize the pipeline well;
- do not assume that either form is faster without evidence.

## Compiler and standard-library choice

Apple Clang uses libc++. A Homebrew GCC uses libstdc++. SDL3 itself is written in C, so SDL3 can be compiled with GCC on macOS. The C++ application, however, uses the standard library of whichever compiler builds it.

Mixing C++ libraries built against libc++ and libstdc++ can produce linker errors or runtime failures because their ABIs differ. Switching the entire project to GCC only to obtain `views::chunk` also changes the C++ standard library for every dependency. That is a large trade for one adaptor.

A newer LLVM/libc++ toolchain may provide `chunk` before Apple's bundled version does. Check `__cpp_lib_ranges_chunk` rather than assuming that a newer compiler implies the library feature. For many projects, the explicit loop is the lower-risk choice.

A third option is range-v3, which provides chunking as an external library. It is reasonable when range composition is used heavily, but unnecessary for a single batch loop.

## Summary

- `std::views::chunk` is a C++23 library feature, and Apple libc++ may not provide it.
- `chunk_by` groups by predicate and is not a fixed-size replacement.
- A manual index loop is a portable fallback for contiguous containers.
- Chunking a filtered view does not make the selected elements contiguous.
- Filtered views can be optimized to zero overhead, but that is not guaranteed; measure hot paths.
- Use ranges for clarity where performance is not critical, and explicit loops where direct control and predictable code generation matter.
