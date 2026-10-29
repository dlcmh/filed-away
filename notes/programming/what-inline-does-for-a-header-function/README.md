# What inline does for a header function

> A DeepSeek conversation on inline as an ODR exception for header definitions and its secondary role as an inlining hint
>
> Source: [shared conversation](https://chat.deepseek.com/share/fta3ttydsjb12zfdhw) on chat.deepseek.com. 1 question, 1 answer. The source link expires when the conversation is deleted from DeepSeek.
>
> Recovered from the shared-conversation HTML export: web citations preserved.

---

## User

What does `inline` do in the following function?

```cpp
// In a "checked access" header. The ONLY place operator[] is used on the
// hot-path array; every other call site goes through this function.
template <typename T, std::size_t N>
[[nodiscard]] inline T& uncheckedAt(std::array<T, N>& a, std::ptrdiff_t i) noexcept {
    // Precondition (caller's responsibility, documented):
    //   0 <= i < static_cast<std::ptrdiff_t>(N)
    return a[static_cast<std::size_t>(i)];   // NOLINT(...)
}
```

---

## DeepSeek

In your code, the `inline` keyword serves two distinct purposes: it acts as a **compiler hint** to suggest inlining for performance, and more importantly, it **relaxes the One Definition Rule (ODR)** to allow the function to be defined in a header file without causing linker errors.

### 🎯 Performance Hint (Inlining)

The `inline` keyword suggests to the compiler that it should attempt to replace calls to `uncheckedAt` with the function's body directly. This eliminates the overhead of a function call (stack frame setup, jumping, returning).[[1]](https://docs.microsoft.com/en-us/cpp/cpp/inline-functions-cpp)[[4]](https://learn.microsoft.com/nl-be/cpp/cpp/inline-functions-cpp?view=msvc-170#inline-__inline-and-__forceinline#1)

However, this is **only a suggestion**. The compiler performs a cost-benefit analysis and may ignore the hint if it deems the function too complex or if inlining would increase code size too much (which can hurt performance via cache misses). For a tiny wrapper like `uncheckedAt`, there is a very high chance the compiler will actually inline it.[[1]](https://docs.microsoft.com/en-us/cpp/cpp/inline-functions-cpp)[[7]](https://www.cs.cornell.edu/courses/cs213/2004fa/lectures/Lecture9/Lecture09.pdf#1#1#1)

### ⚖️ The One Definition Rule (ODR) Exemption

This is the critical technical reason `inline` is necessary here. The comment says this is in a **"checked access" header**. If you include a header containing a function definition in multiple `.cpp` files (translation units), the linker will normally complain about **multiple definition errors** (violating the ODR).[[2]](https://wiki.sei.cmu.edu/confluence/pages/diffpagesbyversion.action?pageId=88046369&originalVersion=55&revisedVersion=79#1)[[5]](https://wiki.sei.cmu.edu/confluence/pages/viewpage.action?pageId=88473685#1)

Marking the function `inline` tells the linker: *"This function may exist in multiple object files, but they are all identical—just pick one and discard the rest."* This allows you to safely define the template function in a header without breaking the build.[[1]](https://docs.microsoft.com/en-us/cpp/cpp/inline-functions-cpp)[[9]](https://gcc.gnu.org/legacy-ml/libstdc++/2015-07/msg00058.html#1)

### 💡 A Note on Templates

You might wonder if `inline` is redundant since it is a template. While function templates have special ODR rules that allow multiple definitions, they are **not** implicitly `inline` in the C++ standard. Adding `inline` explicitly is safe and, as noted by GCC developers, can help the compiler decide to inline it and reduce the number of symbols exported in the binary.[[6]](https://gcc.gnu.org/pipermail/gcc-help/2024-October/143765.html)[[9]](https://gcc.gnu.org/legacy-ml/libstdc++/2015-07/msg00058.html#1)

---

### Summary

For your specific `uncheckedAt` function:

- **`inline`** ensures you don't get linker errors when this header is included in multiple source files.
- It **hints** the compiler to optimize away the call overhead, which is desirable for a hot-path accessor.
