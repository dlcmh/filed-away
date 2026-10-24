# Where the asterisk goes in a C++ pointer declaration

> Based on a DeepSeek conversation about `CA::MetalLayer* layer` versus `CA::MetalLayer *layer` in metal-cpp: [shared conversation](https://chat.deepseek.com/share/9w2iaxs5uw93g80z7p).

Both declarations introduce the same type:

```cpp
CA::MetalLayer* layer = ...;
CA::MetalLayer *layer = ...;
```

The compiler interprets both as “`layer` is a pointer to `CA::MetalLayer`.” The position of the asterisk relative to the type name or variable name has no effect on the resulting type, the generated code, or the program's behavior.

## The grammar behind the two forms

A declaration contains a type specifier and one or more declarators. In `CA::MetalLayer *layer`, the type specifier is `CA::MetalLayer` and the declarator is `*layer`. Whitespace around the asterisk is insignificant, so `CA::MetalLayer* layer` is parsed identically.

The distinction is therefore stylistic. The two common readings are:

- `CA::MetalLayer* layer` treats the asterisk as part of the type: “the type is pointer-to-`CA::MetalLayer`.” This is common in C++ code.
- `CA::MetalLayer *layer` treats the asterisk as part of the declarator: “`*layer` is a `CA::MetalLayer`.” This is common in C code and in conventions that emphasize the declarator.

Neither reading changes what the compiler does. The choice is a readability convention.

## The multiple-declaration trap

The difference becomes visible when one declaration introduces several variables:

```cpp
CA::MetalLayer *first, *second;  // both are pointers
CA::MetalLayer* first, second;   // first is a pointer; second is an object
```

The asterisk belongs to each declarator, not to the type specifier. In the second line, only `first` receives the `*`; `second` is an ordinary `CA::MetalLayer` object. If that type has no default constructor, the line does not compile; if it does, the two variables have different types despite the shared type name.

This is the strongest practical argument for either placing the asterisk with the variable or, preferably, declaring one variable per line. A type alias also removes the ambiguity:

```cpp
using MetalLayerPtr = CA::MetalLayer*;

MetalLayerPtr first, second;  // both are pointers
```

## A related but distinct issue: `const`

Asterisk placement does not affect meaning, but `const` placement does:

```cpp
const CA::MetalLayer* layer = nullptr;       // pointer to const CA::MetalLayer
CA::MetalLayer* const fixedLayer = nullptr;  // const pointer to CA::MetalLayer
```

The first declaration prevents modifying the pointed-to object through `layer`. The second prevents reassigning `fixedLayer` itself. This distinction should not be confused with the stylistic choice between `Type* name` and `Type *name`.

## In metal-cpp

`CA::MetalLayer` is metal-cpp's C++ interface for Apple's `CAMetalLayer`. A declaration such as `CA::MetalLayer* layer` is a pointer to that wrapper object. Both asterisk placements are accepted by the compiler and by metal-cpp; the library does not impose a style.

For a codebase, the useful rule is consistency:

- Choose one placement and enforce it with the project's formatter.
- Declare one variable per declaration, or use a type alias when several pointers share a type.
- Keep `const` placement explicit and deliberate.

## Summary

`CA::MetalLayer* layer` and `CA::MetalLayer *layer` are the same declaration. The asterisk is part of the declarator, not the type specifier, which is why multiple declarations expose a meaningful difference. Single-variable declarations, a consistent style, and a formatter remove the ambiguity without changing the code's meaning.

## References

- cppreference.com, [Declarations](https://en.cppreference.com/w/cpp/language/declarations).
- DeepSeek, [shared conversation](https://chat.deepseek.com/share/9w2iaxs5uw93g80z7p).
