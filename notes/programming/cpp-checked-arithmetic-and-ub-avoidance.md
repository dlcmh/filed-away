# C++ how to: checked arithmetic — libraries, compiler flags, and automatic strategies for numeric UB

The absolute-value and sum notes each ended at the same place: a correct
result requires guarding the operations against unrepresentable values, and
the guards must be written by hand. This note surveys what exists so the
guard does not have to be: libraries of checked operations, compiler flags
that change what arithmetic means, and language features that make the
guarantees automatic.

The catalog of numeric undefined behavior this addresses:

- signed overflow in `+`, `-`, `*`, and negation (including `-INT_MIN`);
- out-of-range conversion to a signed type (before C++20's mandated
  two's-complement *representation* — which still leaves the *conversion*
  implementation-defined pre-C++20, and defined-but-wrapping only since
  C++20 for unsigned, with signed conversion remaining
  implementation-defined until P0907's model landed in C++20);
- division by zero and `INT_MIN / -1` (the only division that overflows);
- shift counts `>=` the width, or shifting into the sign bit.

## Libraries

### Boost.SafeNumerics

`boost/safe_numerics/safe_integer.hpp` replaces the built-in types with
checking wrappers. Any operation that could produce an unrepresentable
result either throws or returns a flagged error, per a policy:

```cpp
#include <boost/safe_numerics/safe_integer.hpp>
using namespace boost::safe_numerics;

safe<int> a = INT_MAX;
safe<int> b = 1;
try {
    safe<int> c = a + b;   // throws (or traps, per exception_policy)
} catch (std::overflow_error const& e) { /* ... */ }
```

The distinctive feature is *interval arithmetic at compile time*: when the
provably-representable ranges of both operands fit, the check is optimized
away entirely, so correctly-typed code pays nothing. The cost is type
proliferation — `safe<int>` is not `int`, and it shows up in signatures.

### SafeInt (Microsoft)

`safeint.h` ships with MSVC and is usable elsewhere (also on GitHub). It is
the checked-integer library with the longest production history (Internet
Explorer era):

```cpp
#include <safeint.h>
using namespace msl::utilities;

SafeInt<int> a = INT_MAX;
SafeInt<int> b = 1;
try {
    SafeInt<int> c = a + b;           // throws SafeIntException
} catch (SafeIntException const&) { /* ... */ }
```

Template-based, header-only, and heavily tuned to collapse to plain
arithmetic plus a single branch.

### Compiler builtins

Clang and GCC provide checked-operation builtins that compute and test in
one step — no separate comparison, no compiler cleverness needed to fuse
them:

```cpp
int r;
bool overflowed = __builtin_add_overflow(a, b, &r);      // also sub, mul
```

They work on any width and any signedness, and are the pragmatic choice
when a dependency is not wanted. Standardization has been proposed
repeatedly (e.g. P0543's neighbor proposals and WG21 study-group papers on
checked integer operations) but nothing has been adopted; treat them as a
portability decision, not a language feature.

## Language and standard-library arrivals

- **C++20 `<numeric>` fixed the divisibility edge**: integer division is
  still UB for a zero divisor, but `INT_MIN / -1` is now defined (the
  quotient is `INT_MIN`; the standard dropped the requirement that the
  mathematical quotient be representable). The negation `INT_MIN % -1`
  is likewise defined to be `0`.
- **C++26 saturation arithmetic** (P0543): `std::add_sat`, `std::sub_sat`,
  `std::mul_sat`, `std::div_sat`, and `std::saturate_cast` clamp to the
  type's bounds instead of overflowing — defined behavior, no exceptions:

  ```cpp
  #include <numeric>          // C++26
  int r = std::add_sat(INT_MAX, 1);   // INT_MAX
  ```

  Saturation is a *policy choice*, not a default: results are wrong-but-
  defined, so it suits DSP/graphics-style code more than accounting.
- **C++26 contracts** (P2900): `contract_assert` precondition checks with
  configurable violation semantics (terminate, abort, custom handler).
  These do not detect overflow by themselves, but they provide a
  standardized, compiler-enforced notation for the hand-written guards
  described in the previous notes.

## Compiler flags: changing what arithmetic means

These are build-wide switches — the strongest form of "automatic", with the
usual caveat that they change the machine the compiler targets:

- `-fwrapv` (GCC, Clang): signed overflow becomes defined two's-complement
  wraparound. This *removes* the UB but keeps the wrong answers; it is what
  a codebase migrating from C historically reached for. It also inhibits
  some optimizations that rely on "signed arithmetic never overflows".
- `-ftrapv` (GCC; Clang historically buggy, superseded): emit a trapping
  check on every signed operation — the program dies at the overflow
  instead of continuing. Zero integration cost, poor diagnostics.
- `-fsanitize=signed-integer-overflow,unsigned-integer-overflow` (part of
  `-fsanitize=undefined`): runtime instrumentation with precise reports.
  Development and CI only — the runtime cost is several-fold on
  arithmetic-dense code. Note `unsigned-integer-overflow` is *not* UB
  (unsigned wraps by definition); the flag exists to surface logic bugs.
- `-D_GLIBCXX_ASSERTIONS` / `-D_LIBCPP_ENABLE_ASSERTIONS=1`: checked
  standard-library internals (out-of-bounds `operator[]`, invalid
  iterators) rather than arithmetic, but part of the same defense-in-depth.
- Static analysis: `-Wsign-conversion`, `-Wconversion`, clang-tidy's
  `bugprone-integer-division` and `cert-int09`-family checks catch the
  conversions *into* bad states at compile time. Clang's
  `-fsanitize=integer` + `-fsanitize-trap` combinations round out the
  runtime matrix.
- UBSan in production: `-fsanitize-undefined-trap-on-error` reduces the
  runtime cost to a single trap instruction per check with no library
  dependency — a middle ground when "crash on overflow" is acceptable in
  production but the sanitizer runtime is not.

## Strategies that need no guards at all

1. **Widen at the boundary.** The sum of two `int`s always fits in
   `long long`; the absolute value of any `int` except `INT_MIN` does too
   (and `INT_MIN` itself is detectable by comparison before any
   arithmetic). Choosing the accumulator type so overflow is
   *unrepresentable* deletes the guard rather than writing it. This is the
   cheapest strategy and the reason `std::accumulate` calls want a
   correctly-typed initial value.
2. **Type-driven safety.** Wrap primitives once, in a small set of domain
   types (`Quantity`, `Index`, `Offset`) whose operators are checked by
   construction (via SafeInt or `safe<int>` underneath). Application code
   then cannot express the unguarded form — the guard is enforced by the
   type system, not by discipline.
3. **Unsigned where the domain is non-negative**, accepting that unsigned
   arithmetic is defined (wrapping) rather than safe: `0u - 1u` is `UINT_MAX`
   by definition, which trades UB for a silently-wrong answer. Combine with
   `-fsanitize=unsigned-integer-overflow` in CI to surface it.
4. **Contracts at API boundaries**: document and enforce (C++26
   `contract_assert`, or plain assertions today) that inputs lie within
   the range where the internal arithmetic is trivially safe. This
   centralizes checking where data enters, instead of at every operation.

## The Rust contrast

Rust is the reference design for "guarantee by mechanism," via four stacked
decisions:

- **Fixed-width primitives**: `i32`/`u64` are 32 and 64 bits by definition,
  everywhere. C++ has had the equivalent (`<cstdint>`) since C++11, but as
  opt-in typedefs beside a default `int` whose width follows the platform ABI.
- **Checked by default**: in debug builds, `a + b` that overflows panics with
  file, line, and operands; in release it wraps as documented policy.
  Per-operation opt-outs cover the full menu — `checked_add` (`Option`),
  `saturating_add` (clamp), `wrapping_add` (explicit wrap), `overflowing_add`
  (result plus flag). No library, no builtins, no flags — one-character-apart
  methods on every integer type.
- **No implicit conversions**: `i32 + i64` is a compile error. The entire
  truncating-`abs` / widening-`fabs` category does not exist.
- **Honest debug/release split**: checks where they will be seen (debug, CI),
  escape hatches where performance requires them.

The one defense for C++: its integer rules underpin fifty years of
ABI, embedded targets, and pre-standard code. Rust had the freedom of a blank
slate. For new code, the C++ mitigations in this note approximate, at the cost
of discipline, what Rust encodes in the type names and method set.

## Choosing among them

| Situation | First choice |
|---|---|
| Fixed narrow domain, trusted inputs | plain arithmetic + UBSan in CI |
| Untrusted integer inputs, exceptions acceptable | Boost.SafeNumerics or SafeInt |
| No dependencies wanted | `__builtin_*_overflow` |
| Multimedia/DSP semantics (clamping is correct) | C++26 `std::*_sat`, or hand clamping today |
| Migrating a legacy codebase off UB today | `-fwrapv` as a stopgap, guards where correctness matters |
| Library API with public inputs | widened domain types + boundary checks |

The pattern across all of them: the goal is not more guards but *fewer
places where correctness depends on remembering to write one* — a wider
type, a checked wrapper, a build flag, or a contract each moves the
guarantee from convention to mechanism.

## Related notes in this collection

- [C++ how to: absolute value of a number](cpp-how-to-absolute-value-of-a-number.md)
- [C++ how to: a function returning the sum of two numbers](cpp-how-to-function-returning-sum-of-two-numbers.md)
