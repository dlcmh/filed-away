# Using GCC 16 alongside Apple Clang on macOS

> Based on a DeepSeek conversation about `std::generator`, Apple libc++, and Homebrew GCC 16: [shared conversation](https://chat.deepseek.com/share/u0f1qgqd6mfh3ypjbt).

`std::generator` is a C++23 library feature that Apple's bundled libc++ has not provided. A Homebrew GCC installation does provide it through libstdc++, but using that compiler on macOS requires care.

## Bare g++ is not GCC

On macOS, the command named `g++` is usually a compatibility shim for Apple Clang:

```bash
g++ --version
# Apple clang version ...
```

Homebrew installs GCC with versioned names:

```bash
ls /opt/homebrew/bin/g++-*
# /opt/homebrew/bin/g++-16
```

The versioned command is the real GCC:

```bash
g++-16 --version
# g++-16 (Homebrew GCC 16.2.0) 16.2.0
```

Calling `g++-16` directly avoids accidentally compiling with Apple Clang.

## A working generator test

```cpp
#include <generator>
#include <iostream>

std::generator<int> iota(int n) {
    for (int i = 0; i < n; ++i) {
        co_yield i;
    }
}

int main() {
    for (int value : iota(5)) {
        std::cout << value << ' ';
    }
    std::cout << '\n';
}
```

Compile and run:

```bash
g++-16 -std=c++23 generator.cpp -o generator
./generator
```

The expected output is:

```text
0 1 2 3 4
```

This confirms three separate things: the `<generator>` header exists, `co_yield` compiles, and range-for can consume the generator.

## What GCC 16 provides

GCC 16 with libstdc++ supplies many C++23 library facilities that Apple libc++ lacks or has not completed. Examples include:

- `std::generator`;
- `<stacktrace>`;
- several range adaptors such as `join_with`, `zip_transform`, and `adjacent_transform`;
- `<print>` and `std::println`;
- `std::expected`, `std::mdspan`, and `std::flat_map` / `std::flat_set`.

Availability still depends on the exact GCC version, so the compiler's feature-test macros remain the authority.

## When to use which compiler

Use Apple Clang for native macOS applications that depend on Apple frameworks, Xcode integration, signing, or system-library ABI compatibility. Apple controls the system's C++ runtime, and switching the entire application to libstdc++ can create link or ABI problems.

Use GCC 16 for portable C++ work, experimentation with newer library features, AI toolchain host code, or projects whose deployment target already uses libstdc++. It is a practical choice when the same code must build on Linux, where GCC is the default.

Avoid changing the global `g++` command through an alias. That silently changes the behavior of scripts and build systems that expect the macOS default.

## CMake integration

Pin the compiler per project with a toolchain file:

```cmake
# toolchain-gcc16.cmake
set(CMAKE_C_COMPILER /opt/homebrew/bin/gcc-16)
set(CMAKE_CXX_COMPILER /opt/homebrew/bin/g++-16)
```

```bash
cmake -B build -DCMAKE_TOOLCHAIN_FILE=toolchain-gcc16.cmake
```

This leaves Apple Clang as the system default and opts only the selected project into GCC.

For editor support, clangd can read the project's `compile_commands.json` and use the GCC flags and headers even when GCC produces the binary.

## Summary

- `g++` on macOS is normally Apple Clang; real Homebrew GCC is `g++-16`.
- GCC 16 + libstdc++ supports `std::generator` and many newer library features.
- Use GCC for portable or frontier C++ projects, and Apple Clang for native macOS integration.
- Select GCC explicitly per project; do not replace the global `g++`.

## Reference

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/u0f1qgqd6mfh3ypjbt).
