# Accessing vector elements: front, back, at, and operator[]

> Based on a DeepSeek conversation about `std::vector::front()`: [shared conversation](https://chat.deepseek.com/share/1ntkwkf8uyxnghvvqd).

`std::vector` provides several ways to reach an element. They differ in what they return, whether they check bounds, and what happens when the vector is empty.

## First and last elements

```cpp
#include <iostream>
#include <vector>

int main() {
    std::vector<int> values{10, 20, 30};

    std::cout << values.front() << '\n';  // 10
    std::cout << values.back() << '\n';   // 30

    values.front() = 99;
    values.back() = 77;

    std::cout << values[0] << '\n';       // 99
    std::cout << values[2] << '\n';       // 77
}
```

Both `front()` and `back()` return a reference, so assignment modifies the element. On a `const` vector, they return a const reference and assignment is rejected.

```cpp
const std::vector<int> values{1, 2, 3};
int first = values.front();  // read-only
// values.front() = 4;       // error
```

`front()` is equivalent to `*begin()`. `back()` is equivalent to `*(end() - 1)`; `end()` itself points one past the last element.

## The empty-vector problem

`front()`, `back()`, and `operator[]` do not check whether the vector is empty. Calling any of them on an empty vector is undefined behavior.

```cpp
std::vector<int> values;

if (!values.empty()) {
    std::cout << values.front() << '\n';
    std::cout << values.back() << '\n';
}
```

An empty check is required before any unchecked access.

## Access table

| Expression | Result | Empty vector | Bounds checked |
| --- | --- | --- | --- |
| `v.front()` | Reference to first element | Undefined behavior | No |
| `v.back()` | Reference to last element | Undefined behavior | No |
| `v[0]` | Reference to first element | Undefined behavior | No |
| `v[v.size() - 1]` | Reference to last element | Underflow and undefined behavior | No |
| `v.at(0)` | Reference to first element | Throws `std::out_of_range` | Yes |
| `v.at(v.size() - 1)` | Reference to last element | Throws `std::out_of_range` | Yes |
| `v.begin()` | Iterator to first element | Valid; may equal `end()` | No |

The `at()` forms are the checked equivalents. They throw `std::out_of_range` rather than invoking undefined behavior.

## at() versus operator[]

`at()` checks the index against the vector size. `operator[]` does not.

Use `at()` when:

- the index comes from user input, a file, or another untrusted source;
- the index calculation is complex or spread across several lines;
- the cost of a failed access is high and an exception is an acceptable response.

Use `operator[]` when:

- the index is already proven valid, such as inside `for (std::size_t i = 0; i < v.size(); ++i)`;
- profiling shows the bounds check matters in a hot path;
- the project enables debug-mode iterator checks, which catch many mistakes during development without release-time cost.

Many standard libraries add debug checks to `operator[]` in debug builds. That provides a middle ground: fast release builds and checked development builds.

The choice is not “always use `at()`.” Bounds checks are a safety tool, not a universal requirement. Redundant checks in a loop whose index is already bounded add code and can add overhead.

## Reference invalidation

A reference returned by `front()`, `back()`, `at()`, or `operator[]` points into the vector's storage. It becomes invalid when an operation reallocates the vector or erases the referenced element.

```cpp
int& first = values.front();
values.push_back(40);  // may reallocate
// first is now invalid
```

Do not retain references across operations that can resize or erase.

## Summary

- `front()` and `back()` return references to the first and last elements.
- They do not check for emptiness; guard with `empty()`.
- `at()` checks bounds and throws `std::out_of_range`.
- `operator[]` does not check; it is appropriate when the index is proven valid.
- References are invalidated by reallocation or erasure.
- Use checked access for untrusted or complex indices, and unchecked access where bounds are already established and performance matters.

## Reference

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/1ntkwkf8uyxnghvvqd).
