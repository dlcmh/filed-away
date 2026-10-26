# A C++23 code review: formatting a grid without manual indexing

> Based on a Gemini conversation, “C++23 Code Review for Grid Serialization”: [shared conversation](https://share.gemini.google/q2LVgM9uMAYE).

The code under review converts a flat character buffer into a newline-separated grid:

```cpp
[[nodiscard]] std::string str() const {
    std::string out;
    out.reserve((width_ + 1) * height_);
    for (usize y = 0; y < height_; ++y) {
        out.append(&cells_[y * width_], width_);
        out.push_back('\n');
    }
    return out;
}
```

Assuming `usize` is an alias for `std::size_t`, the function is correct and efficient. A C++23 review would still suggest changes, mainly for clarity and safety rather than speed.

## What the code already does well

- `out.reserve((width_ + 1) * height_)` allocates the exact final size once. The loop performs no reallocation.
- The function is `const` and `[[nodiscard]]`; it is a read-only query whose result should not be ignored.
- The runtime cost is O(width × height), which is unavoidable for producing the full string.

A rewrite should preserve the reservation. Replacing it with repeated `operator+=` or `push_back` without a reserve would be a regression.

## What a C++23 reviewer would change

The manual index and address arithmetic:

```cpp
&cells_[y * width_]
```

requires the reader to reconstruct the row layout. It also mixes the row index, the width, and a pointer into one expression. If `width_` or `height_` changes type, or if the buffer size and dimensions drift apart, the loop can read the wrong region.

C++23 provides a chunking view for this shape of data:

```cpp
#include <ranges>
#include <string>

[[nodiscard]] std::string str() const {
    std::string out;
    out.reserve((width_ + 1) * height_);

    for (auto row : cells_ | std::views::chunk(width_)) {
        out.append(row.begin(), row.end());
        out.push_back('\n');
    }

    return out;
}
```

`std::views::chunk(width_)` treats the flat buffer as consecutive rows of `width_` elements. `row` is a subrange, and `append(row.begin(), row.end())` appends the row without naming a pointer offset. The reservation and the single allocation remain.

## Toolchain caveat

`std::views::chunk` is a C++23 library feature, not merely a C++23 language feature. A compiler that accepts `-std=c++23` does not necessarily provide it.

At the time of writing, the Apple Clang/libc++ toolchain used for this review does not define `__cpp_lib_ranges_chunk`, and the chunk version above does not compile there. The feature macro can be checked before relying on it:

```cpp
#if defined(__cpp_lib_ranges_chunk)
// chunk-based implementation
#else
// fallback
#endif
```

A portable C++20 fallback keeps the row boundary explicit without raw pointer arithmetic:

```cpp
#include <span>

[[nodiscard]] std::string str() const {
    std::string out;
    out.reserve((width_ + 1) * height_);

    const std::span<const char> grid{cells_};
    for (std::size_t y = 0; y < static_cast<std::size_t>(height_); ++y) {
        const auto row = grid.subspan(
            y * static_cast<std::size_t>(width_),
            static_cast<std::size_t>(width_));
        out.append(row.data(), row.size());
        out.push_back('\n');
    }

    return out;
}
```

This version makes the row slice explicit, preserves the reservation, and works without `views::chunk`.

## Was the original code using pointer decay?

The review described `&cells_[y * width_]` as pointer decay. That description is inaccurate. The expression is an address-of operation:

- `cells_` is a `std::vector<char>`.
- `cells_[index]` is a `char` lvalue.
- `&cells_[index]` is a `char*` pointing at that character.

There is no array-to-pointer decay in that expression. `std::string::append(const char*, std::size_t)` accepts a pointer and a count, which is why the call works. The concern is manual pointer arithmetic and an implicit length, not decay.

Array-to-pointer decay occurs when an array is used in most expressions or passed to a function:

```cpp
int values[5] = {1, 2, 3, 4, 5};

std::size_t a = sizeof(values);  // 5 * sizeof(int)

int* p = values;                  // array decays to pointer
std::size_t b = sizeof(p);        // pointer size, not array size
```

A function parameter written as an array is adjusted to a pointer:

```cpp
void print(int values[]);   // adjusted to int*
void print(int* values);    // same parameter type
```

The array's extent is not preserved by the decay. That is a separate issue from the grid loop.

## Preconditions and edge cases

- `width_` must be greater than zero before using `views::chunk(width_)`. A zero chunk size is invalid.
- `width_` and `height_` should be converted consistently to `std::size_t`; mixing signed and unsigned arithmetic can produce surprising conversions.
- `reserve((width_ + 1) * height_)` assumes the multiplication does not overflow. For realistic grid sizes this is safe, but a library accepting arbitrary dimensions should validate it.
- The code appends a newline after every row, including the last. If the last newline is not wanted, the final row needs separate handling.

## When the original loop is acceptable

The manual loop is not wrong. It is appropriate when:

- the project must compile on a standard library without `views::chunk`;
- the code is performance-sensitive and the pointer-and-length append has been measured as the better option;
- the loop is small, local, and protected by tests.

The main improvement is not a different algorithm. It is making the row boundary visible and eliminating arithmetic that the type system cannot check.

## Summary

A C++23 rewrite can express the grid as `std::views::chunk(width_)`, but the standard library must implement that facility. On a toolchain without it, a `std::span`-based row loop is a safe fallback. The original code's `&cells_[...]` is pointer-to-element arithmetic, not pointer decay; `reserve` and the O(N) cost should be preserved either way.
