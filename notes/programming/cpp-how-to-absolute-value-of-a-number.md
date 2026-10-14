# C++ how to: absolute value of a number

Quick reference for getting `|x|` in C++, including the traps.

## Integers: `std::abs` from `<cstdlib>`

```cpp
#include <cstdlib>

int a = std::abs(-5);        // 5
long b = std::abs(-7L);      // picks the long overload
long long c = std::abs(-9LL);
```

`std::abs` is overloaded per integer type, so there is no silent widening.

## Floating point: `std::abs` from `<cmath>`

```cpp
#include <cmath>

double x = std::abs(-3.14);  // 3.14
float  y = std::abs(-2.5f);
```

For floating point, prefer `std::abs` over the C name `std::fabs` — same behavior, but `fabs` has no overload for integer types (it converts to `double`).

## The traps

1. **`INT_MIN` has no positive counterpart.** `std::abs(INT_MIN)` is undefined behavior (the result `-2147483648` cannot be represented as a positive `int`). The same applies to `LLONG_MIN` and every other integer type's most-negative value. Guard it:

   ```cpp
   if (v == std::numeric_limits<int>::min()) { /* handle specially */ }
   ```

   Or compute in a wider type: `std::abs(static_cast<long long>(v))` — still wrong for `LLONG_MIN` itself.

2. **The C `abs` eats floats.** `#include <cstdlib>` + `abs(-3.14)` truncates to `int` and returns `3` — no diagnostic. Keep `<cstdlib>` for integers and `<cmath>` for floats, and keep the `std::` prefix: with `using namespace std;` and both headers included, the overloads disambiguate; with the C headers (`<stdlib.h>`, `<math.h>`) they do not.

3. **`fabs` on an int widens.** `std::fabs(-5)` returns `5.0` as a `double`. Harmless in comparisons, wrong when you need an integer.

4. **Unsigned types need no abs.** `-u` on an unsigned is well-defined (modulo arithmetic) and already "positive"; `std::abs` has no unsigned overload, so calling it invites an implicit conversion you did not want.

## Beyond scalars

- `std::abs` also works on `std::complex` and `std::valarray` (both from `<complex>`/`<valarray>`), returning the modulus for complex numbers.
- For difference-as-distance, prefer the well-tested form:

  ```cpp
  int dist = std::abs(a - b);            // fine if a-b can't overflow
  auto dist2 = std::abs(long(a) - b);    // widen when a, b span extremes
  ```

- C++20's `std::midpoint` / C++23's `std::abs` overloads for fixed-width types do not change the `INT_MIN` rule: it is still UB when the magnitude cannot be represented.
