# Prefix and postfix increment in C++ loops

> A DeepSeek conversation on when ++i and i++ are interchangeable in C++ loops, iterator costs, and why older code favors i++
>
> Source: [shared conversation](https://chat.deepseek.com/share/sunbmz5w3kxlwxgyld) on chat.deepseek.com. 2 questions, 2 answers. The source link expires when the conversation is deleted from DeepSeek.
>
> Recovered from the shared-conversation HTML export: tables preserved.

---

## User

In C++ index loops, can we always write either `++i` or `i++`, or does it depend on the type of loop?

---

## DeepSeek

# `++i` vs `i++` in C++ Loop Indexes

**Short answer:** For standard index loops (`for (int i = 0; i < n; ++i)`), you can *usually* use either interchangeably — but not *always*, and it's not purely about loop type.

## When they're interchangeable

For **built-in types** (`int`, `size_t`, pointers, etc.) in a simple increment-by-one loop:

```cpp
for (int i = 0; i < n; ++i)   // fine
for (int i = 0; i < n; i++)   // fine, identical behavior
```

The compiler optimizes away the temporary for `i++` on built-in types, so there's no performance difference. The loop behavior is identical because you don't use the return value.

## When it matters (or at least differs)

### 1. Iterators / user-defined types

For iterators and class types, `i++` creates and returns a temporary copy; `++i` doesn't. In a loop where you ignore the result, **prefer `++i`**:

```cpp
for (auto it = v.begin(); it != v.end(); ++it)  // preferred
for (auto it = v.begin(); it != v.end(); it++)  // works, but makes a copy
```

Modern compilers may optimize this away too, but `++i` is the idiomatic choice.

### 2. When the loop condition uses the value

Here the *type of loop* (really, *how you use the variable*) matters:

```cpp
int i = 0;
while (i++ < 5) { ... }   // compares OLD value, then increments
while (++i < 5) { ... }   // increments, then compares NEW value
```

These have genuinely different behavior. Same for:

```cpp
arr[i++] = x;   // uses i, then increments
arr[++i] = x;   // increments, then uses i
```

### 3. Range-based `for`

`for (auto x : container)` has no increment expression at all — neither applies.

## Rule of thumb

| Situation | Use |
| --- | --- |
| Simple `for (…; …; X)` index loop, built-in type | Either is fine |
| Iterator / class type | Prefer `++i` |
| Loop condition or body depends on old vs. new value | Choose deliberately |
| Range-based for | N/A |

So: **it depends less on the "type of loop" and more on (a) the type of the counter and (b) whether you rely on the pre-/post-increment return value.** For the common `for` index loop over an integer, you can always use either.

---

## User

I might be remembering it wrongly, but `i++` did seem to be the more prevalent form.

---

## DeepSeek

# You're remembering correctly — `i++` *is* historically more prevalent

That's not a false memory. In older / textbook / C-style code, `i++` shows up more often. A few reasons:

## Why `i++` looks more common

1. **C heritage.** `i++` reads naturally as "i plus plus" and was the idiomatic form in K&R C and most C textbooks. A lot of code inherited that style.
2. **`i++` is the "name" of the operator.** The postfix form is literally what people say out loud ("increment i"), and it's the classic example in early C material.
3. **Loop code you'll encounter in the wild** is often written by people coming from C, Java, or older C++ codebases, where `i++` dominates:

   ```cpp
   for (int i = 0; i < n; i++)  // extremely common in real code
   ```

## But note the C++ community's nudge

Within modern C++ specifically, there's a well-known stylistic push toward **`++i`**:

- **Scott Meyers, *Effective C++*** (Item 6 in early editions): "Distinguish between prefix and postfix forms of increment and decrement operators" — recommends prefix for user-defined types.
- **Google C++ Style Guide** and **C++ Core Guidelines** lean toward prefix (`++i`) for the reasons we discussed (no temporary).
- So a lot of *guideline-following* C++ code uses `++i`, while a lot of *real-world / legacy / tutorial* code uses `i++`.

## The practical takeaway

- **In actual codebases**, `i++` is probably still the more frequently *seen* form, especially in `for` loops over integers.
- **In style guides for modern C++**, `++i` is the more frequently *recommended* form.
- Neither is "wrong" for an integer index loop — they compile to the same thing.

So your memory isn't faulty: `i++` is the more prevalent *observed* form. The `++i` preference is more of a best-practice recommendation than a reflection of what most code actually looks like.
