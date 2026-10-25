# The nodiscard attribute in C++: a short guide

`[[nodiscard]]` is a C++17 attribute that tells the compiler to warn when a function's return value is ignored. It does not change behavior, ABI, or performance. It makes a likely mistake visible at compile time.

```cpp
[[nodiscard]] int width() const { return width_; }
```

```cpp
canvas.width();                    // warning: return value ignored
int w = canvas.width();            // fine
static_cast<void>(canvas.width()); // explicit discard, no warning
```

The attribute is placed before the function declaration, usually before the return type. For a member function, the same placement applies:

```cpp
class Canvas {
public:
    [[nodiscard]] int width() const;
    [[nodiscard]] int height() const;
};
```

## When to use it

Use `[[nodiscard]]` when discarding the result is almost always a bug:

- **Pure queries.** `width()`, `height()`, `size()`, and `empty()` return information that the caller requested.
- **Error codes and status results.** A discarded `bool` or error enum can hide a failed operation.
- **Factory functions.** Ignoring a returned `std::unique_ptr` destroys the object immediately.
- **Expensive computations.** A function that builds a string, buffer, or result should not be called and ignored accidentally.
- **Lookup functions.** A failed lookup result must be checked.

```cpp
[[nodiscard]] bool save(const std::string& path);
[[nodiscard]] std::unique_ptr<Widget> make_widget();
```

## When not to use it

Do not apply it to every function. If ignoring the result is a normal, intentional use, the annotation produces noise.

- Functions called primarily for side effects, such as logging, where the return value is optional.
- Compatibility functions whose return value is routinely ignored.
- `void` functions, where there is no result to discard.

A deliberate discard can be written as `static_cast<void>(expression)`. That documents the decision and suppresses the warning.

## What the compiler does

`[[nodiscard]]` requests a diagnostic; it does not force the caller to use the value. GCC and Clang typically report it under `-Wunused-result`, which is often enabled by `-Wall`. MSVC reports C4834. With `-Werror`, the warning becomes an error.

The attribute belongs on the declaration that callers see. For a function declared in a header and defined in a `.cpp` file, place it on the declaration in the header. Repeating it on the definition is unnecessary.

C++20 permits an explanatory message:

```cpp
[[nodiscard("check the returned error code")]] bool save(const std::string& path);
```

The message is a diagnostic aid, not part of the function type.

## Relationship to clang-tidy

clang-tidy's `modernize-use-nodiscard` check suggests the attribute for const member functions and other functions whose return value is normally meaningful. Apply the suggestion selectively; the check identifies candidates, not obligations. A function returning a value for side-effect logging is a poor candidate even if the check flags it.

The [macOS alien-fleet tutorial](macos-character-mode-alien-fleet.md) marks `width()`, `height()`, `bottom()`, `str()`, and a private bounds helper with `[[nodiscard]]`. These are pure queries, so ignoring their results would be a mistake.

## Summary

- `[[nodiscard]]` warns when a return value is discarded.
- It is compile-time only and has no runtime cost.
- Use it for queries, error codes, factories, and expensive results.
- Avoid it where ignoring the result is intentional.
- Put it on the declaration callers include.
