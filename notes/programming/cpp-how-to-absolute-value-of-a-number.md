# C++ how to: absolute value of a number

Quick reference for getting `|x|` in C++, including the pitfalls.

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

## Pitfalls

1. **`INT_MIN` has no positive counterpart.** `std::abs(INT_MIN)` is undefined behavior (the result `-2147483648` cannot be represented as a positive `int`). The same applies to `LLONG_MIN` and every other integer type's most-negative value. Guard it:

   ```cpp
   if (v == std::numeric_limits<int>::min()) { /* handle specially */ }
   ```

   Or compute in a wider type: `std::abs(static_cast<long long>(v))` — still wrong for `LLONG_MIN` itself.

2. **The C `abs` truncates floating-point arguments.** `#include <cstdlib>` + `abs(-3.14)` converts to `int` and returns `3` — no diagnostic. Keep `<cstdlib>` for integers and `<cmath>` for floats, and keep the `std::` prefix: with `using namespace std;` and both headers included, the overloads disambiguate; with the C headers (`<stdlib.h>`, `<math.h>`) they do not.

3. **`fabs` on an int widens.** `std::fabs(-5)` returns `5.0` as a `double`. Harmless in comparisons, wrong when you need an integer.

4. **Unsigned types need no abs.** `-u` on an unsigned is well-defined (modulo arithmetic) and already non-negative; `std::abs` has no unsigned overload, so calling it produces an implicit conversion that is rarely intended.

## Beyond scalars

- `std::abs` also works on `std::complex` and `std::valarray` (both from `<complex>`/`<valarray>`), returning the modulus for complex numbers.
- For difference-as-distance, prefer the well-tested form:

  ```cpp
  int dist = std::abs(a - b);            // fine if a-b can't overflow
  auto dist2 = std::abs(long(a) - b);    // widen when a, b span extremes
  ```

- C++20's `std::midpoint` / C++23's `std::abs` overloads for fixed-width types do not change the `INT_MIN` rule: it is still UB when the magnitude cannot be represented.

## Sanitizers detect; boundaries defend

Running `absolute_value(INT_MIN)` under `-fsanitize=undefined` (or `-fsanitize=signed-integer-overflow`) reports `negation of -2147483648 cannot be represented in type 'int'` at runtime — invaluable in development. But sanitizers are compile-time opt-in and are not enabled in production builds, so an `INT_MIN` arriving from user input, a file, or a network message once again wraps around silently. On two's-complement hardware, negating `0x80000000` yields `0x80000000` again, so the function appears to work and returns `INT_MIN` — an incorrect result that is plausible on its face, and precisely the form of undefined behavior that is hardest to detect in the field.

If the function accepts values from outside, guard it at the boundary. The options, from most explicit to least:

1. **Guard the negation and pick a policy** for the impossible case:

   ```cpp
   #include <climits>

   int absolute_value(int x) {
       if (x == INT_MIN) throw std::domain_error("abs(INT_MIN)");  // or abort(), or return INT_MIN under a documented contract
       return x < 0 ? -x : x;
   }
   ```

   Returning `INT_MIN` is what most real code effectively does, but it is mathematically inconsistent (|−2³¹| ≠ −2³¹), so throwing or aborting is the well-defined choice.

2. **Widen the domain**: take and return `long long`, negating through the wider type. That fixes `INT_MIN`-of-`int` inputs entirely; only `LLONG_MIN` remains pathological and worth documenting.

3. **Delegate to `std::abs`** — and note it has the *same* UB. The standard library does not guard this for you; the hand-rolled version is no worse.

Related literal pitfall: `int my_num = -2147483648;` does not do what it appears to — the literal `2147483648` does not fit in `int`, so it becomes `long` (or triggers a warning), and the negation applies to that. It happens to produce `INT_MIN` on common platforms, but the portable spelling is `INT_MIN` from `<climits>`. The constant for the undefined-behavior case is exactly where the literal form is least reliable.

The general pattern: sanitizers catch what your test inputs happen to trigger; validation at the boundary catches what the world actually sends you.

