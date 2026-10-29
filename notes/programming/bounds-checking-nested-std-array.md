# Bounds-checking nested std::array access

> Based on a DeepSeek conversation about `cppcoreguidelines-pro-bounds-constant-array-index` and `std::ssize()`: [shared conversation](https://chat.deepseek.com/share/nwzzvlkr9lh054b8b0).

A deep subscript expression such as:

```cpp
int x = values[a][b][c][d][e];
```

can produce several clang-tidy warnings on one line. The warning is emitted once for each subscript that uses a runtime index on an unchecked array.

## Which subscripts are checked?

The `cppcoreguidelines-pro-bounds-constant-array-index` check applies to raw C arrays and to `std::array` subscripts that reach an unchecked array access. A `std::vector` subscript does not trigger this particular check, although `.at()` is still the safer choice when the index is not already proven.

For a nested `std::array`:

```cpp
using Dim5 = std::array<int, 10>;
using Dim4 = std::array<Dim5, 10>;
using Dim3 = std::array<Dim4, 10>;
using Dim2 = std::array<Dim3, 10>;
using Dim1 = std::array<Dim2, 10>;

Dim1 values{};

int x = values[a][b][c][d][e];
```

Each runtime subscript is a separate unchecked access. clang-tidy reports five diagnostics at different columns on the same line.

An index that is a constant expression is exempt, because the compiler can verify it:

```cpp
constexpr std::size_t i = 3;
int x = values[i][b][c][d][e];  // the first subscript is checked at compile time
```

## Use .at() at every level

The checked form chains `.at()` through every dimension:

```cpp
int x = values.at(a).at(b).at(c).at(d).at(e);
```

Each `.at()` returns a reference to the next array, so the next subscript still needs its own check. Fixing only the final subscript leaves the outer accesses unchecked.

If an index is out of range, `.at()` throws `std::out_of_range`. That is useful in tests and ordinary game logic where the access is not in a measured hot path.

An explicit bounds check is also accepted by the linter:

```cpp
if (a >= values.size()) {
    return;
}

auto& level4 = values[a];

if (b >= level4.size()) {
    return;
}

auto& level3 = level4[b];
// Continue with checked or proven accesses.
```

For deeply nested arrays, the `.at()` chain is shorter and harder to get wrong.

## Signed indices and std::ssize

`std::array::at()` and `operator[]` take an unsigned `std::size_t`. Comparing a negative `int` with `.size()` converts the negative value to a large unsigned value:

```cpp
int i = -1;

if (i < values.size()) {
    // The comparison converts i to std::size_t.
}
```

`std::ssize()` returns the size as a signed type, usually `std::ptrdiff_t`, so the comparison remains signed:

```cpp
#include <iterator>

if (i < std::ssize(values)) {
    // -1 < 10 is true; the negative index can be rejected explicitly.
}
```

`std::ssize` is available in C++20. It is a better fit than `size()` when the index is signed.

## Hot loops with proven bounds

If a loop has already established that every index is in range, an unchecked access may be appropriate:

```cpp
#include <array>
#include <cstddef>
#include <iterator>

struct Particle {
    float x = 0.0f;
    float y = 0.0f;
    float vx = 0.0f;
    float vy = 0.0f;
    bool alive = true;
};

std::array<Particle, 4096> particles{};

void updateParticles(float dt) {
    const std::ptrdiff_t count = std::ssize(particles);

    for (std::ptrdiff_t i = 0; i < count; ++i) {
        // Bounds are proven by the loop condition.
        // NOLINTNEXTLINE(cppcoreguidelines-pro-bounds-constant-array-index)
        Particle& p = particles[static_cast<std::size_t>(i)];

        if (!p.alive) {
            continue;
        }

        p.x += p.vx * dt;
        p.y += p.vy * dt;
    }
}
```

The cast is safe because `i` is in `[0, count)` and `count` equals `particles.size()`. The comment states the invariant; the named `NOLINTNEXTLINE` suppresses only that check on the following line. A bare `NOLINT` would suppress too much.

This pattern is justified only when the bounds have actually been proven. It should not be used to silence a warning around an unchecked index of unknown origin.

## Prefer iterators when no index is needed

If the loop does not need the index, iterators avoid the subscript question entirely:

```cpp
for (Particle& p : particles) {
    if (!p.alive) {
        continue;
    }

    p.x += p.vx * dt;
    p.y += p.vy * dt;
}
```

There is no array subscript to warn about, and the range is defined by the container.

## When both the index and the element are needed

C++23 provides `std::views::enumerate`, which pairs each element with its index:

```cpp
#include <ranges>

for (auto&& [index, p] : particles | std::views::enumerate) {
    if (!p.alive) {
        continue;
    }

    p.x += p.vx * dt;
    p.y += p.vy * dt;
}
```

This avoids the manual counter and the unchecked `operator[]` entirely. The index has the range's difference type, typically `std::ptrdiff_t`, so it is signed and does not introduce a signed/unsigned comparison. The element binding refers to the original array element; `auto&&` makes that explicit, and modifications to `p` affect `particles`. The project test uses `auto [i, p]` and mutates `p` successfully, confirming the reference behavior.

`enumerate` solves the case where both the position and the element are required. It does not replace `.at()` for an independent indexed access, and it does not help with nested subscripts unless each level is separately available as a range.

### Toolchain availability

`std::views::enumerate` is a C++23 library feature guarded by `__cpp_lib_ranges_enumerate`, not merely by C++23 language support. Availability depends on which libc++ the build selects.

At the time of writing:

- Apple Clang 21.0.0 with the system libc++ does not define the macro, and the loop fails to compile.
- Homebrew LLVM 23.1.4 defines `__cpp_lib_ranges_enumerate` as `202302` and compiles the loop.

The current CMake build directory for this project uses `/opt/homebrew/opt/llvm/bin/clang++`. The `tester` target, which compiles `apps/tetris/test.cpp`, builds and runs successfully. That test uses `std::views::enumerate`, so the feature is available in this project as configured.

`CMakeLists.txt` itself only sets the C++23 language mode. It does not select Homebrew LLVM; that compiler is recorded in the CMake cache. A clean build using system Apple Clang would lose the feature. Configure such a build explicitly:

```text
-DCMAKE_CXX_COMPILER=/opt/homebrew/opt/llvm/bin/clang++
```

For a project that must support both toolchains, guard the feature:

```cpp
#if defined(__cpp_lib_ranges_enumerate)
for (auto&& [index, p] : particles | std::views::enumerate) {
    // ...
}
#else
const std::ptrdiff_t count = std::ssize(particles);
for (std::ptrdiff_t index = 0; index < count; ++index) {
    // Proven-bounds access with a documented NOLINT.
}
#endif
```

With the current Homebrew LLVM configuration, the `std::views::enumerate` loop is the cleaner option when both the index and the element are needed. The `std::ssize()` loop remains the fallback for Apple Clang.

## When to use which

| Situation | Approach |
| --- | --- |
| Ordinary access, index not proven | `.at()` or an explicit bounds check |
| Signed index compared with a container size | `std::ssize(container)` |
| Hot loop, no index needed | Range-based `for` or iterators |
| Hot loop, index and element needed, `enumerate` available | `std::views::enumerate` |
| Hot loop, index needed and bounds proven | `operator[]` with a named `NOLINT` and a documented invariant |

For a small board or configuration array, `.at()` is usually the right default. For a measured inner loop over thousands of elements, prove the bounds once and keep the unchecked access localized.

## Summary

- A nested subscript can generate one warning per runtime array access.
- `.at()` must be applied at every level; each level returns another array.
- Constant indices are exempt because the compiler can verify them.
- Use `std::ssize()` when an index is signed.
- Use unchecked access only when the loop has proven the bounds, and document the suppression.
- Use iterators when the index itself is not needed.
- Use `std::views::enumerate` when both index and element are needed and the library provides it;
  the current Homebrew LLVM build does, while system Apple Clang does not.
- Fall back to the `std::ssize()` loop when `__cpp_lib_ranges_enumerate` is absent.

## Reference

- DeepSeek, [shared conversation on bounds checking](https://chat.deepseek.com/share/nwzzvlkr9lh054b8b0).
- DeepSeek, [shared conversation on `std::views::enumerate`](https://chat.deepseek.com/share/i8du7wi6khk81sx1dm).
