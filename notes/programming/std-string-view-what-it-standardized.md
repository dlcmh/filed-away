# What `std::string_view` standardized

> Based on a DeepSeek conversation about the pre-C++17 ancestors of `std::string_view`: [shared conversation](https://chat.deepseek.com/share/rkpetrda5makowiujh).

`std::string_view` is a non-owning view of a contiguous sequence of characters. Conceptually, it stores a pointer and a length; it does not copy the characters and does not manage their lifetime.

A function can accept a view without requiring a `std::string` allocation:

```cpp
#include <iostream>
#include <string>
#include <string_view>

void print(std::string_view text) {
    std::cout << text << '\n';
}

int main() {
    std::string owned = "Pac-Man";
    print(owned);     // views owned's buffer
    print("ghosts");  // views the string literal
}
```

Neither call creates a temporary `std::string`. The function parameter refers to storage that belongs to `owned` or to the literal.

A view can also refer to part of a string without copying it:

```cpp
std::string_view text = "hello world";
std::string_view first = text.substr(0, 5);  // "hello"
```

`substr` returns another view. The characters remain in the original storage.

## The lifetime rule

A view does not extend the lifetime of the characters it refers to. The source storage must outlive the view:

```cpp
std::string_view view;
{
    std::string local = "temporary";
    view = local;
}
// local has been destroyed; view is now dangling
```

Returning a view of a local string has the same problem:

```cpp
std::string_view makeView() {
    std::string local = "temporary";
    return local;  // invalid: the returned view would dangle
}
```

Modifying or destroying the source `std::string` can also invalidate an existing view. In particular, an operation that reallocates the string's buffer invalidates all views into the old buffer.

## Before C++17

Before `std::string_view` was standardized, C++ code used several approaches for the same concept. The following table summarizes their main properties.

| Approach | Strength | Limitation |
| --- | --- | --- |
| Pointer plus length (for example, `llvm::StringRef`) | No allocation; supports substrings | Each library defined its own type and semantics |
| Pointer pair (`begin`, `end`) | Works with any iterator range | Verbose; loses the "this is a string" meaning |
| `const std::string&` | Familiar string interface | Constructing a `std::string` for a literal or buffer can allocate and copy |
| `const char*` | Simple for C-style strings | Requires null termination; cannot represent a substring without copying or a separate length |

LLVM's `StringRef`, Boost's `string_ref` and `string_view`, and Abseil's `string_view` are well-known examples of the pointer-and-length design. The standard type generalized an existing, proven idea rather than introducing a new representation.

## What standardization added

Standardizing the type provided one shared definition with consistent behavior:

- **Content comparison.** Two views compare equal when their character sequences are equal, not when their pointers are equal.
- **Hash support.** `std::hash<std::string_view>` allows a view to be used as a hash-table key. The underlying characters must still outlive the table entries.
- **Interoperation.** A `std::string` or a null-terminated `const char*` can convert implicitly to a view, which makes the type convenient for function parameters.
- **A clear name.** The word "view" communicates that the object refers to existing storage; it does not own or extend it.
- **Standard operations.** Member functions such as `substr`, `find`, `remove_prefix`, and `remove_suffix` provide common string operations without allocation.
- **A documented contract.** The danger of dangling views was documented prominently. The standard did not make lifetime errors impossible.

The last point is important. `std::string_view` standardizes the representation and the interface, not the lifetime management. The programmer remains responsible for ensuring that the underlying characters remain valid.

## Practical guidance

- Use `std::string_view` for read-only function parameters when the function does not need to store or modify the text.
- Use `std::string` when the function must own the characters, return them, or keep them beyond the call.
- A temporary `std::string` passed directly to a function taking a view remains valid for the duration of that call. Do not keep the view after the call returns.
- Do not return a view of a local object.
- Do not assume that a view is null-terminated. `data()` points to the first character; it does not guarantee a `'\0'` after the last character. If a C API requires a null-terminated string, create a `std::string` from the view.
- Be careful with containers whose keys are views. The container stores the views, not the characters; the source strings must outlive the container.
- A `std::string_view` provides read-only access to its characters. It does not prevent other code from modifying or reallocating the source string.

## Summary

`std::string_view` is a standard, non-owning pointer-and-length view of character data. It replaces several library-specific string-reference types and avoids copies for read-only interfaces. It does not replace `std::string` when ownership is required, and it does not remove the need to reason about the lifetime of the source storage.

## Reference

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/rkpetrda5makowiujh).
