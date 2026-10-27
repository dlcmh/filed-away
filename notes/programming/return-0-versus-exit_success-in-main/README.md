# return 0 versus EXIT_SUCCESS in main

> A DeepSeek conversation on whether return EXIT_SUCCESS is preferable to return 0 in a modern C++ main function
>
> Source: [shared conversation](https://chat.deepseek.com/share/aillej9m8xh6j95i0t) on chat.deepseek.com. 1 question, 1 answer. The source link expires when the conversation is deleted from DeepSeek.
>
> Recovered from the shared-conversation HTML export: web citations preserved.

---

## User

Is `return EXIT_SUCCESS;` preferable to just `return 0;` in modern C++ `int main() { ... }`?

---

## DeepSeek

In modern C++ (C++11 and later), for an `int main()` function, **`return 0;` is typically the better and more common choice**. It is more concise, does not require additional headers, and has exactly the same effect as `return EXIT_SUCCESS;` according to the C++ standard. However, if your code also uses `EXIT_FAILURE` to indicate errors, using `EXIT_SUCCESS` for symmetry is also a reasonable stylistic choice.

### Both Have the Same Effect

According to the C++ standard, returning `0` from `main` is completely equivalent to returning `EXIT_SUCCESS`, and both indicate successful program termination.[[3]](https://stackoverflow.com/revisions/867607f1-a451-41b2-a061-f4039b57c6b8/view-source)[[5]](https://stackoverflow.com/revisions/47f393d3-665f-45be-bd87-7b90488da492/view-source)[[15]](https://stackoverflow.com/questions/7255644/what-is-the-correct-value-to-return-to-the-operating-system-upon-the-successful?rq=3#1)

Specifically, when `main` executes `return 0;`, it is equivalent to calling `std::exit(0)`. The standard specifies that when the `exit` function receives `0` or `EXIT_SUCCESS`, it returns an implementation-defined form of successful termination to the host environment. In other words, on the vast majority of systems (such as POSIX, Windows), `EXIT_SUCCESS` is defined as `0`, but even if it is defined as another value on some rare platform, `return 0;` will still be correctly recognized as success.[[1]](https://stackoverflow.com/posts/79895683/revisions#1)[[3]](https://stackoverflow.com/revisions/867607f1-a451-41b2-a061-f4039b57c6b8/view-source)-

### Why `return 0;` is More Recommended

1. **More Concise, No Header Required**: Using `EXIT_SUCCESS` requires including the `<cstdlib>` header, while `return 0;` requires no additional inclusion. For a simple `main` function, this is a small but practical advantage.[[6]](https://browse.library.kiwix.org/content/stackoverflow.com_en_all_nopic_2022-07/questions/8867871/should-i-return-exit-success-or-0-from-main#1)[[8]](https://stackoverflow.com/revisions/56cbe952-ea6c-4b94-83ae-6f70c0a493b3/view-source)
2. **More Consistent with Implicit Return**: In C++ and in C99 and later, if `main` reaches the end without an explicit return statement, the compiler will implicitly insert `return 0;`. Explicitly writing `return 0;` is consistent with this default behavior.[[6]](https://browse.library.kiwix.org/content/stackoverflow.com_en_all_nopic_2022-07/questions/8867871/should-i-return-exit-success-or-0-from-main#1)[[8]](https://stackoverflow.com/revisions/56cbe952-ea6c-4b94-83ae-6f70c0a493b3/view-source)
3. **No Semantic Ambiguity**: Although beginners might find "0 means success" counterintuitive, this is already a deeply ingrained convention in the C/C++ ecosystem, and any experienced developer understands this.[[2]](https://stackoverflow.com/questions/8867871/should-i-return-exit-success-or-0-from-main#1)[[3]](https://stackoverflow.com/revisions/867607f1-a451-41b2-a061-f4039b57c6b8/view-source)

### When to Choose `EXIT_SUCCESS`

If your program needs to **explicitly indicate failure** (using `EXIT_FAILURE`), then writing `return EXIT_SUCCESS;` is a good choice to maintain **semantic symmetry** and code readability, as both are macros defined by the standard library with clear meanings.[[6]](https://browse.library.kiwix.org/content/stackoverflow.com_en_all_nopic_2022-07/questions/8867871/should-i-return-exit-success-or-0-from-main#1)[[8]](https://stackoverflow.com/revisions/56cbe952-ea6c-4b94-83ae-6f70c0a493b3/view-source)

In short, `return 0;` is entirely sufficient for simple successful program termination; if your code needs to handle both success and failure states, then using paired `EXIT_SUCCESS` / `EXIT_FAILURE` will make the code intent clearer.
