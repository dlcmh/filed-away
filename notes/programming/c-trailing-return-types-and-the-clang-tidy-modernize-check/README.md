# C++ trailing return types and the clang-tidy modernize check

> When C++11 introduced trailing return types, an opinionated comparison of std::printf styles, and the clang-tidy use-trailing-return-type check that enforces the style anyway
>
> Sources: [part 1](https://chat.deepseek.com/share/byl7fa0xkyqbbndzmb), [part 2 — disabling the lint in VS Code](https://chat.deepseek.com/share/0yu24utkegxufscxw0), on chat.deepseek.com. 4 questions, 4 answers. The source links expire when the conversations are deleted from DeepSeek.
> Recovered from the shared-conversation HTML export: web citations preserved.

---

## User

when were trailing return types introduced in c++

---

## DeepSeek

Trailing return types were introduced in **C++11**[[1]](https://isocpp.org/blog/2013/06/trailing-return-types-sumi-cj)[[2]](http://releases-origin.llvm.org/18.1.8/tools/clang/tools/extra/docs/clang-tidy/checks/modernize/use-trailing-return-type.html)[[3]](https://raw.githubusercontent.com/Dr-Sergey/learn_cpp/575e0775d6aa9df1b80d1343af811215cf9c1745/01_Core_Language_Fundamentals/Understand_trailing_return_types_and_when_they_are_required.md#1).

### 🔍 Why They Were Introduced

Before C++11, you could not use function parameters to determine the return type. For example, this was not possible because `a` and `b` are not yet in scope at the point where the return type is declared:

```cpp
// Invalid in C++03
template<class T>
decltype(a * b) mul(T a, T b) { // a and b not in scope
    return a * b;
}
```

Trailing return types solve this by moving the return type **after** the parameter list, where the parameters are in scope:

```cpp
// Valid in C++11
template<class T>
auto mul(T a, T b) -> decltype(a * b) {
    return a * b;
}
```

In C++11, this was sometimes the **only** way to express a return type that depends on the parameters[[3]](https://raw.githubusercontent.com/Dr-Sergey/learn_cpp/575e0775d6aa9df1b80d1343af811215cf9c1745/01_Core_Language_Fundamentals/Understand_trailing_return_types_and_when_they_are_required.md#1)[[5]](https://github.com/Dr-Sergey/learn_cpp/blob/main/01_Core_Language_Fundamentals/Understand_trailing_return_types_and_when_they_are_required.md#1).

### 📌 Later Simplification

C++14 introduced automatic return type deduction (`auto` without a trailing return type), which eliminated the need for trailing return types in most everyday cases[[5]](https://github.com/Dr-Sergey/learn_cpp/blob/main/01_Core_Language_Fundamentals/Understand_trailing_return_types_and_when_they_are_required.md#1).

---

## User

what's your opinion on:

```c++
#include <cstdio>
int main() {
    int x = 0;
    if (x > 0) std::printf("Positive.\n");
    else if (x < 0) std::printf("Negative.\n");
    else std::printf("Zero.\n");
}
```

vs

```c++
#include <cstdio>
using std::printf;
auto main() -> int {
    int x = 0;
    if (x > 0) { printf("Positive.\n"); }
    else if (x < 0) { printf("Negative.\n"); }
    else { printf("Zero.\n"); }
}
```

---

## DeepSeek

Honest take: **the first version is better**, and the second one is mostly cargo-culting C++11 features without a good reason.

Let me break down each difference:

### 1. `auto main() -> int` vs `int main()`

The trailing return type here buys you **nothing**. `main`'s return type is always `int`, and there's no parameter-dependent type to deduce. This is a classic case of "you can, but should you?" — and the answer is no. `int main()` is clearer and universally recognized.

Trailing return types shine when:

- The return type depends on parameters (`decltype(a * b)`).
- You're writing generic code where consistency matters.

For `main`? It's noise.

### 2. `using std::printf;` vs `std::printf(...)`

Both are defensible, but the `using` declaration is only worth it if you're calling `printf` multiple times in a scope. Here, it's called three times, so it's arguably fine. But:

- Inside `main`, a local `using` is fine.
- `std::printf` is more explicit and self-documenting.
- A `using`-declaration at namespace scope in a header is a bad idea; inside `main` it's harmless.

Honestly this is the most defensible change, but it's a wash.

### 3. Braces on single-statement branches

This one is a **real** stylistic split:

- **First version**: compact, idiomatic, common in C/C++ textbooks and older code.
- **Second version**: safer against future edits (you can't accidentally add a second statement outside the branch), and matches what most style guides (Google, LLVM, etc.) recommend.

I lean toward **braces always** for the safety argument, but it's not a correctness issue.

### Overall verdict

Version 2 takes two *good* C++11 features (trailing return types, `auto`) and applies them in a place where they add **zero value**, while making the code longer and less idiomatic for `main`. It reads like someone learned about trailing return types and wanted to use them somewhere.

If you want a modernized version, this is what I'd actually write:

```c++
#include <cstdio>

int main() {
    int x = 0;
    if (x > 0) {
        std::printf("Positive.\n");
    } else if (x < 0) {
        std::printf("Negative.\n");
    } else {
        std::printf("Zero.\n");
    }
}
```

Braces for safety, `std::printf` for clarity, plain `int main()` because that's what it is.

**Rule of thumb:** use a feature when it *solves a problem*, not because it exists.

---

## User

damn llvm team https://clang.llvm.org/extra/clang-tidy/checks/modernize/use-trailing-return-type.html

---

## DeepSeek

Yeah, that clang-tidy check is... a choice. 😄

You're right to point at it, and it actually *reinforces* my earlier point rather than contradicting it. Look at what the docs themselves say:

> **"This transformation is purely stylistic."**

That's the LLVM team telling you on the record: there is no correctness, performance, or expressiveness benefit here. It's a cosmetic rewrite. And then they ship it as a `modernize-*` check, which carries an implicit "this makes your code more modern/better" connotation. It doesn't.

### The check even documents its own footguns

The "Limitations" section is wild for a *purely stylistic* transform:

- It can't handle function pointers, member function pointers, or member pointers.
- It has a real **name-lookup hazard**: rewriting `S f(unsigned S)` to `auto f(unsigned S) -> S` silently changes which `S` is meant, because now the parameter `S` is in scope at the point of the return type. The doc literally shows the rewritten code **failing to compile**.
- They admit they only partially guard against this ("can currently only detect and avoid a clash with a function parameter name").

So a stylistic-only check ships with a documented ability to break your code via unqualified-name capture. That's a lot of downside for zero upside.

### Why it exists at all

This is the "Google/LLVM house style" leaking into a lint rule. Some codebases (notably parts of Google's C++ style in that era) adopted "always use trailing return types" as a uniformity rule — the argument being that it makes function signatures consistent, and that `auto f(...) -> T` reads left-to-right with the name up front. It's a *taste* argument, and if your whole codebase commits to it, uniformity has some value.

But:

- It fights `decltype(auto)`, `auto` deduction, and readability for the 95% of functions where the return type is a plain type.
- It makes `main`, constructors-adjacent helpers, and simple accessors noisier.
- LLVM itself does **not** uniformly use trailing return types in its own code — this check is opt-in for a reason.

### The bigger lesson

`clang-tidy`'s `modernize-*` checks are a **menu, not a mandate**. A lot of teams enable `modernize-use-auto`, `modernize-use-trailing-return-type`, etc. wholesale and then wonder why their diffs are noisy and their `main` looks like a template metaprogramming exercise.

My rule stands: enable a check when it fixes a real problem in your code. For trailing return types, the only real problem they solve is *parameter-dependent return types* — and even that is largely obsolete since C++14's return type deduction. So for most codebases, `modernize-use-trailing-return-type` is best left **off**, or set to only flag the cases where it actually matters (which the check doesn't distinguish).

So: the LLVM team didn't prove me wrong — they wrote you a config knob and told you in the first sentence that it's cosmetic. Whether to flip it is a style-guide decision, and my opinion is still "no, thanks."

---

## User

how to disable this lint in vscode

---

## DeepSeek

To disable the `modernize-use-trailing-return-type` lint in VS Code, the method you use depends on whether you are using the **Microsoft C/C++ extension** or the **clangd extension**.

### 🛠️ If you are using the Microsoft C/C++ extension

You can disable this specific check directly in your VS Code settings.

- **Via the Settings UI**: Open your `settings.json` (Ctrl+Shift+P > "Preferences: Open User Settings (JSON)") and add the check name to the disabled list. The check name is `modernize-use-trailing-return-type`[[11]](https://blog.csdn.net/once_day/article/details/146770641?ops_request_misc=elastic_search_misc&request_id=ca1d10ad644f49628056e45c5a74ff73&biz_id=0&utm_medium=distribute.wap_search_result.none-task-blog-2~all~ElasticSearch~search_v2-11-146770641-null-null.wap_first_rank_v2_rank_v29&utm_term=clang%20object-c#2)[[15]](https://github.com/microsoft/vscode-cpptools/discussions/9759#1).

  ```json
  {
    "C_Cpp.codeAnalysis.clangTidy.checks.disabled": [
      "modernize-use-trailing-return-type"
    ]
  }
  ```

- **Or, use the Quick Fix**: When you see the warning squiggly, hover over it, click "Quick Fix" (or press Ctrl+.), and select the option to **Disable this check**. This will automatically add it to your settings [[11]](https://blog.csdn.net/once_day/article/details/146770641?ops_request_misc=elastic_search_misc&request_id=ca1d10ad644f49628056e45c5a74ff73&biz_id=0&utm_medium=distribute.wap_search_result.none-task-blog-2~all~ElasticSearch~search_v2-11-146770641-null-null.wap_first_rank_v2_rank_v29&utm_term=clang%20object-c#2).

### 🛠️ If you are using the clangd extension

`clangd` reads its configuration from a `config.yaml` file rather than VS Code's `settings.json`.

1. Open the Command Palette (Ctrl+Shift+P) and run **`clangd: Open project configuration file`**[[10]](https://stackoverflow.com/questions/77006517/how-to-display-problems-only-for-the-code-i-changed-added-in-visual-studio-cod#1).
2. In the file that opens, add the following under `ClangTidy` to remove this specific check [[10]](https://stackoverflow.com/questions/77006517/how-to-display-problems-only-for-the-code-i-changed-added-in-visual-studio-cod#1):

   ```yaml
   Diagnostics:
     ClangTidy:
       Remove: 'modernize-use-trailing-return-type'
   ```

3. Restart the clangd server (Ctrl+Shift+P > `clangd: Restart server`) for the change to take effect.

### 💡 Alternative: A project-wide `.clang-tidy` file

If you want to disable this check for your entire project (for anyone who uses clang-tidy with it), you can create or edit a `.clang-tidy` file in your project root [[4]](https://manpages.debian.org/trixie/clang-tidy/clang-tidy.1.en.html#1)[[9]](https://stackoverflow.com/feeds/question/74349432#1)[[15]](https://github.com/microsoft/vscode-cpptools/discussions/9759#1).

Add the following line to disable just this check:

```yaml
Checks: '-modernize-use-trailing-return-type'
```

If you want to disable **all** clang-tidy checks for the project, you can set it to `Checks: '-*'`[[9]](https://stackoverflow.com/feeds/question/74349432#1)[[13]](https://docs.rs/cpp-linter/2.0.0-rc15/cpp_linter/cli/struct.TidyOptions.html#1).

### ⚠️ A note on `NOLINT` comments

You can also suppress the warning on a specific line by adding a comment, but this is generally discouraged as it clutters the code [[5]](https://fuchsia.dev/fuchsia-src/development/languages/c-cpp/lint?hl=en)[[12]](https://chromium.googlesource.com/chromium/src/+show/refs/tags/81.0.4044.115/docs/clang_tidy.md#1)[[19]](https://chromium.googlesource.com/experimental/chromium/src/+/299ad0d85a8885380c77940cbc08606c6b0a9c1c/docs/clang_tidy.md#1).

```cpp
// NOLINTNEXTLINE(modernize-use-trailing-return-type)
int f1();
```
