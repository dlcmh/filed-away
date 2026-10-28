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

## A concrete example: a status query

clang-tidy often suggests `[[nodiscard]]` for a pure status query:

```cpp
class SdlGuard {
public:
    [[nodiscard]] bool ok() const { return ok_; }

private:
    bool ok_ = true;
};
```

Calling `ok()` without using the result is almost certainly a mistake:

```cpp
sdl.ok();                     // typically warns: return value ignored
if (!sdl.ok()) { /* ... */ }  // fine
const bool good = sdl.ok();   // fine
```

The function exists only to report state. It has no side effect that would make the call meaningful on its own, so the return value is the point of the call. The same reasoning applies to `empty()`, `size()`, comparison operators, and functions that return an error code.

It does not apply to every function that returns a value. A mutating function may return a secondary result that callers legitimately ignore, such as the number of erased elements. Marking such a function `[[nodiscard]]` would produce noise. The question is whether ignoring the result is a normal use or a likely bug.

Many SDL3 functions that report failure, including initialization and window creation, are already marked `[[nodiscard]]`; that is why the `if (!SDL_Init(...))` pattern is necessary rather than merely stylistic.

## What the compiler does

`[[nodiscard]]` requests a diagnostic; it does not force the caller to use the value. GCC and Clang typically report it under `-Wunused-result`, which is often enabled by `-Wall`. MSVC reports C4834. With `-Werror`, the warning becomes an error.

The attribute belongs on the declaration that callers see. For a function declared in a header and defined in a `.cpp` file, place it on the declaration in the header. Repeating it on the definition is unnecessary.

C++20 permits an explanatory message:

```cpp
[[nodiscard("check the returned error code")]] bool save(const std::string& path);
```

The message is a diagnostic aid, not part of the function type.

## Relationship to clang-tidy

clang-tidy's `modernize-use-nodiscard` check operates on the declaration, not on a call site. It proposes `[[nodiscard]]` for a non-template, non-variadic `const` member function that returns a non-void value, has no pointer or non-const reference parameters, and is not a member of a class with mutable members. Such a function has no visible way to change state except through an external effect, so the check treats its return value as the likely purpose of the call.

This is a heuristic. The check does not observe a discarded return value and does not know the programmer's intent; it flags the declaration because the signature matches the pattern. In `Canvas::width()`, the `const` qualifier and the `int` return are sufficient evidence. The same rule does not apply to a function that performs I/O or mutates external state.

Apply the suggestion selectively. The check identifies candidates, not obligations. A function returning a value for side-effect logging is a poor candidate even if the check flags it.

Clangd displays these diagnostics when clang-tidy integration is enabled; the diagnostic prefix `clang-tidy(...)` identifies the source. The compiler itself does not warn about a discarded return value until the function carries `[[nodiscard]]` or an equivalent compiler-specific attribute.

See the [clang-tidy documentation](https://clang.llvm.org/extra/clang-tidy/checks/modernize/use-nodiscard.html) for the full list of conditions.

The [macOS alien-fleet tutorial](macos-character-mode-alien-fleet.md) marks `width()`, `height()`, `bottom()`, `str()`, and a private bounds helper with `[[nodiscard]]`. These are pure queries, so ignoring their results would be a mistake.

## Summary

- `[[nodiscard]]` warns when a return value is discarded.
- It is compile-time only and has no runtime cost.
- Use it for queries, error codes, factories, and expensive results.
- Avoid it where ignoring the result is intentional.
- Put it on the declaration callers include.

## Source

- DeepSeek, [shared conversation on `ok()` and `[[nodiscard]]`](https://chat.deepseek.com/share/9j9l3f66uk4p6o686d).
