# const auto versus an explicit enum type

> Based on a DeepSeek conversation about `const auto` and `const PieceType` for a simple enum: [shared conversation](https://chat.deepseek.com/share/6y7eg8up93foscapvt).

A short scoped enum has an obvious type:

```cpp
enum class PieceType {
    I, O, T, S, Z, J, L
};
```

Both declarations below create the same value:

```cpp
const PieceType piece = PieceType::T;
const auto deduced = PieceType::T;
```

For this case, the explicit type is usually the better choice.

## Why spell out the type?

The type name is short, and the reader does not have to inspect the initializer to learn what `piece` is.

`auto` is most valuable when it removes noise or avoids repeating a complicated type. Here it removes only five characters and makes the declaration less informative. It also provides no safety benefit: `PieceType::T` already has exactly the type `PieceType`, so there is no implicit conversion to guard against.

There is no performance difference either. Both forms produce the same compiled code.

The general principle is to use type deduction when it makes the code clearer, not merely to avoid typing. For a simple enum, the explicit type is clearer.

## When auto is preferable

`auto` is appropriate when the exact type is verbose, unimportant to the reader, or difficult to spell:

```cpp
const auto first = container.begin();
const auto result = make_widget();
```

The first example avoids writing a long iterator type. The second avoids naming a factory return type that may change.

`auto` is also useful when the initializer's type is the result of a complex expression and restating it would add risk of mistakes. The important question is whether the reader benefits from seeing the type or is better served by a shorter declaration.

## Enums and the underlying integer

Do not use `auto` or a cast merely to extract the integer value behind a scoped enum. C++23 provides `std::to_underlying`:

```cpp
#include <utility>

const int value = std::to_underlying(PieceType::T);
```

`std::to_underlying` returns the enum's underlying integer type without hard-coding that type in the call site. It is safer than guessing `int` or using a C-style cast.

If the code needs the underlying integer for serialization, array indexing, or a protocol field, `to_underlying` states the intent directly.

## A practical rule

- Use `const PieceType piece = PieceType::T;` when the type is short and meaningful.
- Use `const auto` when the type is long, implementation-defined, or irrelevant to the surrounding logic.
- Use `std::to_underlying` when the integer representation itself is required.
- Do not choose between them for performance; the compiled result is the same.

## Summary

For a simple enum such as `PieceType`, the explicit type improves readability and has no downside. `const auto` is a tool for hiding unnecessary type complexity, not a universal default. C++23's `std::to_underlying` is the direct way to obtain an enum's integer value.

## Reference

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/6y7eg8up93foscapvt).
