# Row-major indexing in a flat grid

> Based on a DeepSeek conversation about `cells_[sz(x + (y * width_))]` versus `cells_[sz((y * width_) + x)]`: [shared conversation](https://chat.deepseek.com/share/3mylfuwboy910gyq8h).

A two-dimensional grid is commonly stored in a one-dimensional buffer in row-major order. The element at column `x` and row `y` is:

```cpp
index = y * width + x;
```

This means “skip `y` complete rows, then move `x` elements into the next row.”

## The two expressions are equivalent

```cpp
x + (y * width_)
(y * width_) + x
```

Addition is commutative, and multiplication has higher precedence than addition. Both expressions compute the same value. Parentheses clarify the intent, but they do not change the order of evaluation.

For a `std::vector<char>`, the assignment is:

```cpp
cells_[static_cast<std::size_t>(y) * width_ + static_cast<std::size_t>(x)] = glyph;
```

Writing `x` first can make the expression read like the coordinate pair `(x, y)`. Writing the row offset first matches the usual formula `y * width + x`. Either is acceptable if the codebase is consistent.

## Performance

There is no meaningful performance difference between the two orderings. Modern compilers optimize both to the same machine code. The multiplication must be computed before the addition in either spelling, and the compiler is free to schedule the independent parts of the expression.

The choice is about readability and consistency, not instruction-level parallelism.

## Convert before multiplying

If `x`, `y`, and `width_` are signed integers, the multiplication can overflow before the result is converted to `std::size_t`. Convert the operands before the arithmetic:

```cpp
const auto index =
    static_cast<std::size_t>(y) * static_cast<std::size_t>(width_) +
    static_cast<std::size_t>(x);

cells_[index] = glyph;
```

If the grid dimensions and coordinates are already `std::size_t`, the casts are unnecessary. Keeping one unsigned type throughout the index calculation avoids signed/unsigned mixing and implementation-defined conversions.

The helper `sz(...)` in the original expression should be applied to the completed index, or the arithmetic should use `std::size_t` directly. Converting only the final result does not protect the multiplication from overflow.

## Centralize the layout

A helper makes the layout rule explicit and keeps it in one place:

```cpp
[[nodiscard]] constexpr std::size_t index(
    std::size_t x,
    std::size_t y,
    std::size_t width) {
    return y * width + x;
}
```

```cpp
cells_[index(x, y, width_)] = glyph;
```

If the storage order ever changes, only the helper changes. Call sites no longer repeat the formula or disagree about operand order.

The helper should also document its preconditions: `x < width`, `y < height`, and `width > 0`. A checked accessor can enforce those conditions before indexing.

## A C++23 alternative

C++23 provides `std::mdspan` for multidimensional views over contiguous storage:

```cpp
#include <mdspan>

std::mdspan<char, std::dextents<std::size_t, 2>> grid(
    cells_.data(),
    static_cast<std::size_t>(height_),
    static_cast<std::size_t>(width_));

grid[y, x] = glyph;
```

This removes the manual index arithmetic entirely. It is useful when the grid is accessed from several places or when the two-dimensional shape is part of the interface. Support depends on the standard library implementation; check `__cpp_lib_mdspan` before relying on it.

## Summary

Both operand orders produce the same row-major index. Prefer a consistent spelling, convert coordinates to `std::size_t` before multiplication, and consider a small `index()` helper to centralize the layout. `std::mdspan` is the stronger abstraction when multidimensional access is common. The performance argument does not distinguish the two expressions.

## Reference

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/3mylfuwboy910gyq8h).
