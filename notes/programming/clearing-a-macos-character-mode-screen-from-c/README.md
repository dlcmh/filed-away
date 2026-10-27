# Clearing a macOS character-mode screen from C++

> A DeepSeek conversation comparing ANSI escapes, std::system, ncurses, and a Rule-of-Five Terminal wrapper for clearing a macOS terminal
>
> Source: [shared conversation](https://chat.deepseek.com/share/f2yoa3630v19g9hnxt) on chat.deepseek.com. 1 question, 1 answer. The source link expires when the conversation is deleted from DeepSeek.
>
> Recovered from the shared-conversation HTML export: the conversation preserved.

---

## User

Show me a few ways a simple macOS C++ character-mode game that might or might not use classes can clear the screen on launch and exit. Ensure that your samples satisfy clang-tidy and also align with the Rule of Five where relevant.

---

## DeepSeek

Here are several ways to clear the screen in a simple character-mode C++ game on macOS, with attention to clang-tidy and Rule of Five compliance.

## Option 1: ANSI Escape Sequence (simplest, no classes)

```cpp
#include <iostream>

int main() {
    // Clear screen + move cursor to home position
    std::cout << "\033[2J\033[H" << std::flush;

    // ... game loop ...

    std::cout << "\033[2J\033[H" << std::flush;
    return 0;
}
```

Pros: no dependencies, no Rule of Five concerns. Cons: requires a terminal that honors ANSI (Terminal.app, iTerm2 both do).

## Option 2: `std::system` calling `clear` (Not recommended but common)

```cpp
#include <cstdlib>
#include <iostream>

int main() {
    if (std::system("clear") != 0) {
        std::cout << "\033[2J\033[H" << std::flush;
    }

    // ... game loop ...

    if (std::system("clear") != 0) {
        std::cout << "\033[2J\033[H" << std::flush;
    }
    return 0;
}
```

clang-tidy will flag `cert-env33-c` / `cppcoreguidelines-pro-type-vararg` style warnings in stricter configs — `std::system` spawns a shell. The ANSI fallback keeps it usable if that check is disabled, but prefer Option 1 or 3.

## Option 3: RAII Terminal Guard (Rule of Five compliant, clang-tidy friendly)

```cpp
#include <iostream>
#include <string_view>

namespace {

constexpr std::string_view kClearHome = "\033[2J\033[H";

class ScreenGuard {
public:
    ScreenGuard() { std::cout << kClearHome << std::flush; }

    // Rule of Five: copy deleted (owns terminal state), move deleted
    // (streaming in a moved-from state is meaningless), destructor restores.
    ScreenGuard(const ScreenGuard&)            = delete;
    ScreenGuard& operator=(const ScreenGuard&) = delete;
    ScreenGuard(ScreenGuard&&)                 = delete;
    ScreenGuard& operator=(ScreenGuard&&)      = delete;

    ~ScreenGuard() {
        std::cout << kClearHome << std::flush;
    }
};

} // namespace

int main() {
    ScreenGuard guard;
    // ... game loop ...
    return 0;
}
```

Rule of Five rationale: because the destructor has a side effect (clearing the screen), the class should not be trivially copyable/movable. Deleting all four special members makes the intent explicit and satisfies `cppcoreguidelines-special-member-functions`.

## Option 4: Same idea, but "Rule of Zero" via `std::unique_ptr` deleter

If you'd rather not write five special members, wrap the cleanup in a unique_ptr with a custom deleter (Rule of Zero):

```cpp
#include <cstdio>
#include <iostream>
#include <memory>

namespace {

void clearScreen() {
    std::cout << "\033[2J\033[H" << std::flush;
}

struct ScreenCleaner {
    void operator()(int*) const noexcept { clearScreen(); }
};

} // namespace

int main() {
    static int dummy = 0;
    std::unique_ptr<int, ScreenCleaner> guard(&dummy);
    clearScreen();

    // ... game loop ...
    return 0;
}
```

This avoids hand-written special members entirely — `unique_ptr` already handles the Rule of Five correctly, and no copy/move ambiguity exists in your own type.

## Option 5: `ncurses` (proper character-mode, most idiomatic)

```cpp
#include <ncurses.h>

namespace {

struct CursesSession {
    CursesSession() {
        initscr();
        cbreak();
        noecho();
        keypad(stdscr, TRUE);
    }

    CursesSession(const CursesSession&)            = delete;
    CursesSession& operator=(const CursesSession&) = delete;
    CursesSession(CursesSession&&)                 = delete;
    CursesSession& operator=(CursesSession&&)      = delete;

    ~CursesSession() { endwin(); }
};

} // namespace

int main() {
    CursesSession session;
    clear();
    refresh();
    // ... game loop with getch(), mvaddch(), etc. ...
    return 0;
}
```

Compile with `clang++ -std=c++20 main.cpp -lncurses`. Note: `ncurses.h` uses macros (`getch`, `clear`) and C-style globals — some aggressive clang-tidy configs (`bugprone-macro-parentheses`, `cppcoreguidelines-pro-bounds-pointer-arithmetic`) can complain; you'd typically add a `.clang-tidy` exclude for that translation unit.

## Notes for clang-tidy / Rule of Five

- Anything holding a resource (terminal state, stream flush on exit) should either delete copy/move (Option 3, 5) or delegate cleanup to an RAII member (Option 4).
- Prefer `"\033[2J\033[H"` over the `CLEAR`/`curses` macros in non-ncurses code — no macro, no global state, no vararg.
- `std::flush` at the end is important — otherwise the sequence may sit in the buffer until the next write, so "launch" clearing can appear late.
- If you use `std::system("clear")`, expect `cert-env33-c` and `bugprone-command-processor` (when the string isn't a literal) to fire.
