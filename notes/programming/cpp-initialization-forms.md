# Value-initialization and the other kinds of C++ initialization

> Based on a DeepSeek conversation about why `SDL_Event event{};` is described as value-initialization: [shared conversation](https://chat.deepseek.com/share/dry4e4dsco4j2gxv64).

“Initialize” is a general word. C++ has several distinct initialization forms, and they differ in which constructor runs and whether the object receives a defined value.

That is why a careful description says **value-initialize** rather than merely **initialize**.

## Why `event{}` is value-initialization

```cpp
SDL_Event event{};
```

The empty braces perform list-initialization. For this C-style type, the empty list resolves to value-initialization, which gives the object a defined zeroed state. The event can then be reused for every `SDL_PollEvent` call without carrying indeterminate bytes into the first call.

The alternative:

```cpp
SDL_Event event;
```

is default-initialization. For a scalar or a trivial aggregate, the members are left indeterminate. Reading them before assignment is undefined behavior.

Writing `SDL_Event event = SDL_Event();` also produces value-initialization, but through copy-initialization syntax. The braces are the shorter and more direct form.

## The main initialization forms

| Form | Example | Key point |
| --- | --- | --- |
| Default-initialization | `int x;` `SDL_Event e;` | Scalar and trivial aggregate members may be indeterminate. Class constructors run. |
| Zero-initialization | `static int x;` | Static and thread-local objects start zeroed before other initialization. |
| Value-initialization | `T{}` `T()` | Zero-initializes or calls the default constructor according to the type. |
| Copy-initialization | `T x = y;` | Uses `=`; cannot call an explicit constructor. |
| Direct-initialization | `T x(y);` `T x{y};` | Can call explicit constructors. |
| List-initialization | `T x{...};` | Brace form; rejects narrowing conversions. |
| Aggregate-initialization | `Point p{1, 2};` | Initializes members of a simple aggregate in order. |
| Reference-initialization | `T& r = obj;` | A reference must bind to an object at declaration. |
| Constant-initialization | `static int x = 42;` | Value is known at compile time; runs before dynamic initialization. |

These categories overlap. List-initialization can resolve to value-initialization or aggregate-initialization. Value-initialization can include zero-initialization. The table names the rule that applies, not a set of mutually exclusive syntaxes.

## What value-initialization guarantees

For a class with a user-provided default constructor, value-initialization calls that constructor.

For a class without a user-provided constructor, or with a trivial default constructor, value-initialization zero-initializes the object first and then applies the remaining rules.

For `SDL_Event`, the practical result is that all members begin in a defined state. That is the useful guarantee behind the braces. Saying only “the braces initialize it” does not communicate that guarantee.

## Practical guidance

- Use `T value{};` for a local object that needs a defined default state.
- Avoid `T value;` for scalar or trivial aggregate types unless every member is assigned before use.
- Use braces for list initialization when narrowing should be rejected.
- Use parentheses or braces when an explicit constructor is required.
- Use `= default` on a constructor only when the member defaults already provide a valid state.

## Summary

“Initialize” describes a broad category. “Value-initialize” names the specific rule that gives `SDL_Event event{};` its zeroed, defined state. The distinction is useful because the alternative, default-initialization, can leave members indeterminate.

## Reference

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/dry4e4dsco4j2gxv64).
