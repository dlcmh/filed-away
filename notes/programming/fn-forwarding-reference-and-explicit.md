# `Fn&&`, value categories, and `explicit`: reading a clang-tidy diagnostic

> Based on a diagnostic about the benchmark harness in the accelerator tutorial: [chapter 1](https://accelerator-tutorial.pages.dev/part-1/01-cpp23-as-a-machine-control-language/) and `labs/ch01/bench.hpp`.

The diagnostic concerned this signature:

```cpp
template <Runnable Fn>
Result measure(Fn&& fn, int warmup = 3, int reps = 10);
```

clang-tidy's `cppcoreguidelines-missing-std-forward` check saw a forwarding reference that was never forwarded and suggested adding `std::forward`. That suggestion would satisfy the check but misunderstand the function.

`measure` calls the callable repeatedly:

```cpp
for (int i = 0; i < warmup; ++i) {
    fn();
}
// ...
for (int i = 0; i < reps; ++i) {
    fn();
}
```

It owns a workload and invokes it many times. It does not forward the callable to another function exactly once. The correct change is to take the callable by value:

```cpp
template <Runnable Fn>
Result measure(Fn fn, int warmup = 3, int reps = 10);
```

The rest of this article explains why.

## Lvalues, rvalues, and references

An **lvalue** is an expression with a stable identity, usually a named object:

```cpp
auto work = [] { /* ... */ };
measure(work);  // work is an lvalue
```

An **rvalue** is a temporary or a value that is about to be discarded:

```cpp
measure([] { /* ... */ });  // temporary lambda, an rvalue
```

References can bind to these categories in different ways:

| Parameter | Accepts lvalue? | Accepts rvalue? | Meaning |
| --- | --- | --- | --- |
| `Fn fn` | Yes, by copy/move | Yes, by move | The function owns its own callable. |
| `Fn& fn` | Yes | No | The function mutates the caller's callable. |
| `const Fn& fn` | Yes | Yes | Read-only access to the callable. |
| `Fn&& fn` | Yes, in a deduced template | Yes | A forwarding reference; preserves the argument's category. |

A non-template `T&&` is an rvalue reference. In a template where `T` is deduced, `T&&` is a **forwarding reference**: it can bind to either an lvalue or an rvalue.

## How `Fn&&` deduces

For:

```cpp
template <Runnable Fn>
Result measure(Fn&& fn);
```

the deduction works like this:

| Call | Deduced `Fn` | Parameter type |
| --- | --- | --- |
| lvalue `work` | `Work&` | `Work&` |
| temporary lambda | `Work` | `Work&&` |

Reference collapsing turns `Fn&&` into `Work&` when `Fn` is already a reference. The final parameter type depends on the call site.

That is useful when the function forwards the argument to another function and must preserve whether it was an lvalue or an rvalue. It is not useful when the function stores or repeatedly uses the object.

## What `std::forward` does

`std::forward<Fn>(fn)` is a conditional cast. It does not move anything by itself. It restores the value category that was deduced:

```cpp
template <class T>
void wrapper(T&& value) {
    consume(std::forward<T>(value));
}
```

If the caller passed an lvalue, `T` is a reference type and `forward` produces an lvalue. If the caller passed an rvalue, `forward` produces an rvalue.

Forwarding is correct when the wrapper is a relay:

```cpp
template <class T>
void relay(T&& value) {
    destination(std::forward<T>(value));  // exactly once
}
```

`measure` is not a relay. It calls `fn()` many times.

## Why forwarding here is wrong

Suppose the callable passed to `measure` is a temporary with a ref-qualified call operator:

```cpp
struct Work {
    void operator()() & {
        // called on an lvalue: reusable
    }

    void operator()() && {
        // called on an rvalue: allowed to consume state
    }
};
```

If `measure` did this on every iteration:

```cpp
std::forward<Fn>(fn)();
```

and `Fn` was deduced as a non-reference type, each call would select `operator()&&`. The first call is allowed to move state out of the callable. Later iterations would invoke a moved-from object.

Even when the callable has only an ordinary `operator() const` and the code happens to work, the forwarding cast misdescribes the function. The callable is not being relayed; it is being stored and invoked repeatedly.

The Core Guidelines rule F.19 says: use a forwarding reference only to forward. Here the parameter should not be a forwarding reference at all.

## Why by value is the right signature

```cpp
template <Runnable Fn>
Result measure(Fn fn, int warmup = 3, int reps = 10);
```

With `Fn fn`:

- A temporary callable is moved into the parameter.
- An lvalue callable is copied into the parameter.
- The function owns a callable for the duration of the measurement.
- `fn()` calls the callable as an lvalue, so a reusable `operator() &` is selected.
- The copy or move happens once, before the timer starts. It is not part of the measured loop.

The alternatives are worse for this contract:

- `Fn&` accepts only lvalues. It rejects the temporary lambdas that callers naturally pass.
- `const Fn&` accepts temporaries but cannot call a `mutable` lambda, whose call operator is non-const.
- `Fn&&` plus `std::forward` would make the signature promise forwarding while the body invokes repeatedly.

A `NOLINT` suppression would hide the mismatch instead of fixing it.

The `Runnable` concept is defined as:

```cpp
template <class Fn>
concept Runnable = std::invocable<Fn&>;
```

It checks that the type can be called as an lvalue. A by-value `Fn` satisfies that requirement in the function body.

## What `explicit` does

The same diagnostic run flagged the allocator's converting constructor:

```cpp
template <class U>
explicit AlignedAllocator(
    [[maybe_unused]] const AlignedAllocator<U, Alignment>& other) noexcept {}
```

`explicit` controls **implicit conversions**.

A constructor that can be called with one argument is normally a converting constructor. Without `explicit`, it can be used in copy-initialization and in implicit conversions:

```cpp
AlignedAllocator<int, 64> a = other_allocator;  // implicit conversion
```

With `explicit`, only direct-initialization is allowed:

```cpp
AlignedAllocator<int, 64> a(other_allocator);   // direct initialization
```

The allocator has a templated constructor so that an allocator for one element type can be converted into an allocator for another element type, as the standard allocator interface expects. That conversion is usually performed explicitly by allocator-aware containers. There is no reason to allow it to happen silently in arbitrary expressions.

`explicit` is therefore a statement of intent: this cross-type construction is available, but it is not an implicit conversion.

The other parts of the constructor are also deliberate:

- `template <class U>` permits conversion from an allocator with a different `value_type`.
- `[[maybe_unused]]` marks the parameter as intentionally unused; this allocator is stateless, so `other` is not read. Naming it documents what it represents.
- `noexcept` states that the conversion cannot throw. Allocator operations are expected to support that guarantee.

An ordinary copy constructor for the same type is separate. `explicit` here applies to the converting constructor template.

## The general lesson

A static-analysis check identifies a construct. It does not know the function's contract.

For `measure`, the construct `Fn&&` suggested "forward me", but the contract said "call me many times". Changing the signature to by-value fixed the contract mismatch. Adding `std::forward` would have made the checker quiet while making the code less correct.

For the allocator, the construct was an implicit converting constructor. `explicit` made the intended conversion boundary clear.

When a diagnostic fires, decide which is wrong: the construct or the contract. Do not apply the suggested patch without checking that it matches what the function is supposed to do.

## Summary

- `Fn&&` in a deduced template is a forwarding reference; it binds to both lvalues and rvalues.
- `std::forward` is a conditional cast used to relay an argument once, not a general-purpose move.
- `measure` invokes its callable repeatedly, so forwarding on each call could invoke a consuming `operator()&&` on a moved-from object.
- `Fn fn` gives the harness ownership and calls the callable as an lvalue; the one copy or move happens before timing.
- `Fn&` rejects temporaries; `const Fn&` rejects mutable lambdas.
- `explicit` prevents implicit conversions through a converting constructor; direct initialization remains available.
- A clang-tidy warning describes a construct, not necessarily the right remedy.

## Reference

- AI Accelerator Craft, [C++23 as a machine-control language](https://accelerator-tutorial.pages.dev/part-1/01-cpp23-as-a-machine-control-language/).
