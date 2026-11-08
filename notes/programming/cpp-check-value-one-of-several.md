# Checking whether a value is one of several values in C++

> Based on a DeepSeek conversation about testing a key against a set of values in C++: [shared conversation](https://chat.deepseek.com/share/fch9t1jp8ladvtyoq6).

Suppose a program must decide whether a value belongs to a short list:

```cpp
char code = 'b';
// true when code is 'a', 'b', or 'c'
```

For a small fixed list, a lookup container is usually unnecessary. The appropriate form depends on whether the list is known at compile time.

## Direct comparison or switch

For two or three values, direct comparison is the clearest choice:

```cpp
if (code == 'a' || code == 'b' || code == 'c') {
    // ...
}
```

For a different action per value, use a `switch`:

```cpp
switch (code) {
case 'a':
case 'b':
case 'c':
    // shared action
    break;
default:
    break;
}
```

The stacked labels are intentional: `'a'` and `'b'` fall through to the body below `'c'`. For a longer list, a data structure is preferable to a long condition.

## Fixed list: constexpr array and find

C++20 provides `std::ranges::find`:

```cpp
#include <algorithm>
#include <array>

constexpr std::array<char, 3> keys{'a', 'b', 'c'};

if (std::ranges::find(keys, code) != keys.end()) {
    // code is one of the keys
}
```

In C++17, use the iterator-pair overload:

```cpp
if (std::find(keys.begin(), keys.end(), code) != keys.end()) {
    // code is one of the keys
}
```

Both forms perform a linear scan without allocation. The array stores its elements directly. The explicit size must match the contents: too few initializers are filled with `'\0'`, which can match accidentally. Class template argument deduction avoids the mismatch:

```cpp
constexpr std::array keys{'a', 'b', 'c'};  // std::array<char, 3>
```

## Fold-expression helper (C++17)

A variadic helper gives list syntax at the call site without a container:

```cpp
template <typename T, typename... Args>
[[nodiscard]] constexpr bool isOneOf(const T& value, const Args&... args) {
    return ((value == args) || ...);
}

if (isOneOf(code, 'a', 'b', 'c')) {
    // ...
}
```

The `||` fold expands to the equivalent comparison chain. The references avoid copies for types such as `std::string`. This form is suitable when the list is written directly at the call site; a named `constexpr` array is easier to share across functions.

## Runtime container

A container is appropriate when the collection is large, changes at run time, or is inserted into and erased dynamically:

```cpp
#include <unordered_set>

const std::unordered_set<char> keys{'a', 'b', 'c'};

if (keys.contains(code)) {
    // ...
}
```

`contains` is available in C++20. Before C++20, use `keys.find(code) != keys.end()` or `keys.count(code) != 0`.

`std::set` keeps its elements ordered and performs a logarithmic lookup. `std::unordered_set` hashes its elements and does not preserve order. Both allocate a node per element; for three fixed values, the array or fold helper is smaller and faster. If a container is used, construct it once rather than once per frame.

## Comparison

| Situation | Appropriate form |
| --- | --- |
| Two or three values | `if` comparison chain |
| A different action per value | `switch` |
| Small fixed list, C++20 | `constexpr std::array` + `std::ranges::find` |
| Small fixed list, C++17 | `constexpr std::array` + `std::find`, or `isOneOf` |
| Large or dynamic collection | `std::unordered_set` or `std::set` |
| Per-frame or other hot path | `switch`, fold helper, or `static constexpr` array; do not construct a container each time |

A C++23 project can use the ranges form and `contains`. Availability alone does not make a node-based container the most appropriate representation of a three-element list.

## Pitfalls

**A braced-init-list is not a container.** This does not compile:

```cpp
// Invalid: a braced-init-list has no begin() or end() member.
std::find({'a', 'b', 'c'}.begin(), {'a', 'b', 'c'}.end(), code);
```

Use a named `std::array`, or construct one `std::initializer_list` object whose lifetime covers the lookup. Both iterators must come from the same object. Also note that `std::find` returns an iterator; compare it with `end()` rather than using it directly as a condition.

**Match the element type.** This compiles because `char` converts to `int`, but the container stores integers:

```cpp
std::unordered_set<int> keys{'a', 'b', 'c'};  // stores 97, 98, 99
```

Use `std::unordered_set<char>` when the values are characters. This avoids implicit conversions and states the intent directly.

**Check the language standard.** `std::ranges::find` and `contains` require C++20. Fold expressions require C++17. Code copied to an older project may not compile.

## Summary

For a small fixed list, direct comparison, a `switch`, a `constexpr std::array`, or the `isOneOf` helper is sufficient. A `std::set` or `std::unordered_set` is appropriate when the collection is large or dynamic, not because the operation is called a membership test.

## Reference

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/fch9t1jp8ladvtyoq6).
