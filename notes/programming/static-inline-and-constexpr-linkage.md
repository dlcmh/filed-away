# static, inline, and constexpr: what each one buys

> Based on a DeepSeek conversation about `static constexpr` versus `constexpr` at namespace scope: [shared conversation](https://chat.deepseek.com/share/vjvt4azj9a33fwvyix).

At namespace scope, these declarations have the same linkage:

```cpp
#include <array>
static constexpr std::array<char, 3> keys = {'a', 'b', 'c'};
constexpr std::array<char, 3> keys = {'a', 'b', 'c'};
```

`constexpr` implies `const`. A namespace-scope `const` variable has internal linkage by default, so `static` is redundant. Both declarations give each translation unit its own private `keys` object.

`static` can still be written to make the internal linkage explicit. It does not change the behavior.

## Sharing one object across translation units

To give the array external linkage and one shared identity across translation units, use `inline`:

```cpp
inline constexpr std::array<char, 3> keys = {'a', 'b', 'c'};
```

C++17 inline variables may be defined in a header and merged by the linker. Every translation unit refers to the same object. This matters when code compares addresses, returns references to the object, or relies on a single instance.

Use `inline constexpr` when the object must be shared. Use `constexpr` or `static constexpr` when a private per-translation-unit copy is sufficient.

## What static inline means

The meaning of `static inline` depends on where it appears.

### At namespace scope

For a function:

```cpp
static inline int clamp(int value, int low, int high) {
    return value < low ? low : value > high ? high : value;
}
```

`static` already gives the function internal linkage, so every translation unit that includes the header gets its own function and there is no multiple-definition error. `inline` is not required for that ODR protection.

`inline` may still be treated as a hint to expand calls at the call site. Modern compilers decide whether to inline based on optimization settings, function size, and call frequency. The keyword does not guarantee inlining.

For a variable at namespace scope, `static` keeps a separate object per translation unit. `inline` does not change that into one shared object. `static inline` therefore does not provide the cross-translation-unit identity that `inline constexpr` provides. It is usually redundant for this purpose.

### As a class member

Both keywords do distinct work:

```cpp
struct Config {
    static inline int value = 0;

    static inline void reset() {
        value = 0;
    }
};
```

`static` means the member belongs to the class, not to an instance. `inline` allows the static data member to be defined inside the class without a separate out-of-class definition, and it permits a function definition in a header to be merged across translation units.

A member function defined inside the class is already implicitly inline. The explicit `inline` is necessary when the definition is outside the class but still in a header.

## The three keywords

| Form | Main effect |
| --- | --- |
| `constexpr` at namespace scope | Implies `const`; internal linkage; per-translation-unit copy |
| `static constexpr` | Explicitly internal linkage; usually redundant |
| `inline constexpr` | External linkage; one shared object across translation units |
| `static inline` function | Internal linkage plus an inlining hint; no ODR need for `inline` |
| `static inline` variable at namespace scope | Internal linkage; not one shared object; usually redundant |
| `static inline` class member | Class association plus an inline definition; both keywords useful |

## Summary

`constexpr` already gives a namespace-scope constant internal linkage. `static` only makes that explicit. `inline constexpr` is the form that gives one shared object across translation units.

In `static inline`, `inline` buys ODR-safe header definitions in class members and a possible inlining hint in functions. At namespace scope, `static` already provides the linkage, so `inline` is often redundant and does not create a shared object.

## Reference

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/vjvt4azj9a33fwvyix).
