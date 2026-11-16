# Why clangd accepts `size_t` without `std::`

> Based on a DeepSeek conversation about `size_t`, `<cstddef>`, and clangd: [shared conversation](https://chat.deepseek.com/share/4xrhoh18r9r48wcrk4).

clangd accepting both `size_t` and `std::size_t` is expected behavior, and it is not specific to C++23. The global name is valid in many C++ standard-library implementations.

## Two headers, two names

`size_t` is provided through two related headers:

- `<cstddef>` is the C++ header. It guarantees `std::size_t` in namespace `std`.
- `<stddef.h>` is the C compatibility header. It places `size_t` in the global namespace, so `size_t` and `::size_t` work.

The C++ standard also permits `<cstddef>` to declare the name in the global namespace as well as in `std`. GCC's libstdc++ and Clang's libc++ commonly do this.

That is why this often compiles:

```cpp
#include <cstddef>

size_t count = 0;       // works with common implementations
std::size_t other = 0;  // guaranteed by <cstddef>
```

The first line is relying on an implementation-permitted global declaration. The second is the portable C++ spelling.

## Why clangd shows no error

clangd parses code with Clang's semantics and sees the same declarations as the compiler. If the standard library exposes a global `size_t`, clangd sees it too.

clangd's symbol index also knows about both forms for header insertion and navigation: global `size_t` is associated with the C header, and `std::size_t` with `<cstddef>`. Its lack of a diagnostic is not extra leniency; the name is present.

The global `size_t` is a long-standing C compatibility feature. It is usually a typedef for an implementation-defined unsigned integer type, such as `unsigned long`.

## Which form should be used?

Prefer:

```cpp
#include <cstddef>

std::size_t count = 0;
```

Reasons:

- `std::size_t` makes the dependency on the C++ standard library explicit.
- It does not depend on the implementation also exposing the global name.
- It avoids collisions with a user-defined `size_t` or another library's global name.
- It is unambiguous in headers and code that uses many namespaces.

The unqualified form is common in C-style code and in code that includes `<stddef.h>`. It is not a bug when the global declaration exists. It is less explicit.

`::size_t` is the explicit way to request the global name, but it has the same portability caveat as unqualified `size_t` unless `<stddef.h>` was included.

## Summary

- `<cstddef>` guarantees `std::size_t`; `<stddef.h>` puts `size_t` in the global namespace.
- C++ implementations may also expose the global name from `<cstddef>`.
- clangd accepts both because both declarations exist, not because C++23 changed the rule.
- Use `std::size_t` with `<cstddef>` for portable, explicit C++ code.

## Reference

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/4xrhoh18r9r48wcrk4).
