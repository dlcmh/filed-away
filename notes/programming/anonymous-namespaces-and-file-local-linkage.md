# Anonymous namespaces and file-local linkage in C++

> Based on a DeepSeek conversation about `namespace { ... }` around a `ScreenGuard` class: [shared conversation](https://chat.deepseek.com/share/vggm17pb018jiexo4g).

An anonymous namespace looks like this:

```cpp
namespace {

constexpr std::string_view kClearHome = "\033[2J\033[H";

class ScreenGuard {
    // ...
};

} // namespace
```

It is also called an **unnamed namespace**. Names declared inside it have **internal linkage**: they are visible throughout the current translation unit, but not from other `.cpp` files.

For this example, `kClearHome` and `ScreenGuard` are implementation details of one source file. Another file can define its own `ScreenGuard` without causing a duplicate-symbol error, because the two classes are distinct entities.

## A .cpp file is not automatically private

A common misconception is that everything in a `.cpp` file is local to that file. That is not how C++ linkage works.

At namespace scope, a function or variable has **external linkage** by default:

```cpp
// a.cpp
int counter = 0;       // external linkage
void helper() { }      // external linkage
```

Another translation unit can declare and use them:

```cpp
// b.cpp
extern int counter;
void helper();

void use() {
    ++counter;
    helper();
}
```

The linker connects the declarations in `b.cpp` to the definitions in `a.cpp`. Being written in a `.cpp` file does not hide either name.

## Linkage, not file location

| Declaration at namespace scope | Linkage |
| --- | --- |
| `int counter = 0;` | External |
| `void helper() { }` | External |
| `constexpr int k = 1;` | Internal |
| `static int counter = 0;` | Internal |
| `namespace { int counter = 0; }` | Internal |
| `inline constexpr int k = 1;` | External |

`constexpr` implies `const`. At namespace scope, a `const` variable has internal linkage by default unless it is also `extern`, `inline`, or a template. Therefore:

```cpp
constexpr std::string_view kClearHome = "\033[2J\033[H";
```

already has internal linkage and is private to its translation unit. Wrapping it in `namespace { }` is not required. It is still reasonable for grouping and for making the file-local intent visible.

By contrast, `inline constexpr` variables have external linkage. That is why they can be defined in a header and shared across translation units.

## Why use an anonymous namespace?

- **Avoids name collisions.** Two `.cpp` files can each have a private `ScreenGuard` or `kClearHome`.
- **Communicates intent.** The namespace marks the contents as implementation details of the file.
- **Applies to types as well as functions and variables.** A class, struct, or alias can be made file-local. A namespace-scope `static` cannot do that.
- **Can help optimization.** The compiler knows the entity is not referenced from another translation unit and may inline or eliminate it more readily. This is an opportunity, not a guarantee.

The older C-style alternative is `static` on a function or variable. It also gives internal linkage, but it cannot be applied to a type. The unnamed namespace is the modern general-purpose form.

## Use it in .cpp files, not shared headers

An anonymous namespace is appropriate in a `.cpp` file for helpers that only that file needs.

Do not define a type shared across translation units inside an anonymous namespace in a header. Each translation unit that includes the header receives a distinct type with internal linkage, which is not what a shared interface requires. Put shared declarations in a header and their definitions in a `.cpp`, or use `inline` where appropriate.

## What large projects do

Anonymous namespaces are common in large C++ codebases, but they are not used uniformly in every file.

Typical uses:

- file-local helper functions and classes;
- constants whose linkage should be explicit;
- small utilities that would otherwise add names to the linker symbol table.

Files that only define externally declared functions, or whose only top-level entity is `main`, may contain no anonymous namespace at all. Both styles are normal. The decision follows whether the file has implementation details that should not be visible elsewhere.

## Summary

- `namespace { ... }` gives its contents internal linkage.
- A `.cpp` file does **not** make namespace-scope names private by default; they usually have external linkage.
- A namespace-scope `constexpr` variable already has internal linkage, so wrapping it is optional.
- Use an anonymous namespace for file-local helper types and functions, especially in `.cpp` files.
- Avoid it in headers for types that must be shared across translation units.
- Use `inline constexpr` when a constant must be shared through a header.

## Reference

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/vggm17pb018jiexo4g).
