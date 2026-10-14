# C++ how to: a function returning the sum of two numbers

A `sum` function looks trivial, which is exactly what makes it a good vehicle
for the language features that matter: overloads, templates, return-type
deduction, and signed overflow.

## The straightforward version

```cpp
int sum(int a, int b) {
    return a + b;
}
```

For `int` inputs this is the correct form. Small trivially-copyable types
such as `int` and `double` are passed by value; references add nothing here
and `const int&` only obscures the signature.

## Supporting other arithmetic types: a template

```cpp
template <typename T, typename U>
constexpr auto sum(T a, U b) {
    return a + b;
}
```

- `auto` return type (C++14) follows the built-in usual arithmetic
  conversions: `sum(1, 2.5)` yields `double`, `sum(1L, 2u)` yields `long`.
- `constexpr` (C++14 for multi-statement bodies; this body qualifies in
  C++11 form as well) allows the call to be evaluated at compile time:

  ```cpp
  static_assert(sum(2, 3) == 5);
  ```

- The two-type template deliberately reproduces the implicit conversions of
  `a + b`. If implicit narrowing is unwanted, constrain with concepts
  (C++20):

  ```cpp
  #include <concepts>

  template <std::integral T, std::integral U>
  constexpr auto sum(T a, U b) { return a + b; }
  ```

## Signed overflow is undefined behavior

`a + b` on signed integers overflows into undefined behavior — the standard
does not guarantee wraparound. Where inputs are untrusted:

- **Compute in a wider type**: `sum(long long)` inputs, or
  `static_cast<long long>(a) + b` for `int` inputs. `long long` is at least
  64 bits, so the sum of two `int` values is always representable.
- **Check before adding** (portable, no wider type needed):

  ```cpp
  #include <climits>

  int checked_sum(int a, int b) {
      if (b > 0 && a > INT_MAX - b) throw std::overflow_error("sum");
      if (b < 0 && a < INT_MIN - b) throw std::underflow_error("sum");
      return a + b;
  }
  ```

  Note the `INT_MIN` mirror image of the absolute-value case: the guard for
  the most-negative value is again the one that needs separate handling.

- **`__builtin_add_overflow`** (Clang, GCC) computes and reports overflow in
  one operation:

  ```cpp
  int r;
  if (__builtin_add_overflow(a, b, &r)) throw std::overflow_error("sum");
  ```

  Standardization is in progress (`std::add_overflow`-style API has been
  proposed); until then it remains a compiler extension, not portable C++.

For floating point there is no UB: `a + b` on `double` overflows to
`±infinity` per IEEE 754, and precision loss rather than wraparound is the
hazard to document.

## Alternatives in the standard library

- `std::plus<>{}(a, b)` — the callable form used with algorithms
  (`std::accumulate`, `std::transform_reduce`); the transparent `<>` form
  deduces the operand types.
- `std::accumulate(v.begin(), v.end(), 0)` — when the actual task is a
  running sum over a range, a loop-free algorithm communicates the intent
  better than a two-argument helper applied repeatedly. Initialize with `0LL`
  (or `0.0`) so the accumulator type matches the expected magnitude.
- `std::midpoint(a, b)` (C++20) — not a sum, but the related average computed
  without the `a + b / 2` overflow that a hand-written sum would introduce.

## Recommendation

- Single fixed type: `int sum(int, int)` — plain by value.
- Mixed or generic inputs: the constrained two-type `constexpr` template.
- External/untrusted integers: widen to `long long`, or use the pre-addition
  guard; a sanitizer build in development confirms the unguarded form's
  undefined behavior, but the boundary check is what production relies on.
