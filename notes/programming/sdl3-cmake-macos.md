# SDL3 with CMake on macOS

> Based on a DeepSeek conversation about a minimal macOS CMake setup for SDL3: [shared conversation](https://chat.deepseek.com/share/fjms9h2hsmjn495m71).

The simplest CMake setup uses SDL3's exported target:

```cmake
cmake_minimum_required(VERSION 3.16)
project(MyMacApp LANGUAGES CXX)

find_package(SDL3 REQUIRED CONFIG)

add_executable(MyMacApp main.cpp)
target_link_libraries(MyMacApp PRIVATE SDL3::SDL3)
```

`SDL3::SDL3` carries the include directories, library path, and platform-specific link dependencies. Linking that target is sufficient for a normal shared-library installation from Homebrew, the official framework, or a vendored build.

## Helping CMake find SDL3

When SDL3 is installed through Homebrew, CMake usually finds it automatically. If it does not, pass the Homebrew prefix:

```bash
cmake -S . -B build -DCMAKE_PREFIX_PATH="$(brew --prefix sdl3)"
```

For the official SDL3 framework, place the framework and its `share` directory in `~/Library/Frameworks` or `/Library/Frameworks`. For a custom location, point `CMAKE_PREFIX_PATH` at the parent directory.

## Vendoring SDL3

To avoid a system-wide dependency, add SDL3 as a subproject:

```cmake
cmake_minimum_required(VERSION 3.16)
project(MyMacApp LANGUAGES CXX)

add_subdirectory(vendored/SDL EXCLUDE_FROM_ALL)

add_executable(MyMacApp main.cpp)
target_link_libraries(MyMacApp PRIVATE SDL3::SDL3)
```

Clone SDL3 into `vendored/SDL` first. The target name remains the same.

## Do Foundation and Cocoa need to be linked manually?

Usually not. SDL3's CMake configuration adds the required Apple frameworks, such as Foundation and Cocoa, as implementation dependencies of `SDL3::SDL3`. The generated pkg-config metadata also lists them as private dependencies. Linking `SDL3::SDL3` consumes them automatically.

The exception is static linking. With `SDL3::SDL3-static`, some system frameworks may not propagate in every configuration. In that case, add the missing frameworks to `target_link_libraries` explicitly.

```cmake
target_link_libraries(MyApp PRIVATE
    SDL3::SDL3-static
    "-framework Foundation"
    "-framework Cocoa"
)
```

Do not add these frameworks preemptively to a normal shared-library build. Duplicating them does not improve the link and can obscure which dependencies SDL already provides.

## App bundles

A command-line executable is sufficient for development. For a normal macOS `.app`, use `MACOSX_BUNDLE`:

```cmake
add_executable(MyMacApp MACOSX_BUNDLE main.cpp)
target_link_libraries(MyMacApp PRIVATE SDL3::SDL3)
```

For distribution, the SDL3 framework or dynamic library must be placed inside the bundle, typically under `Contents/Frameworks`. The official SDL3 framework guide describes copying the shared target into the bundle.

## Summary

- Use `find_package(SDL3 REQUIRED CONFIG)`.
- Link `SDL3::SDL3`; it supplies include paths, libraries, and Apple framework dependencies.
- Set `CMAKE_PREFIX_PATH` when CMake cannot locate a Homebrew or framework installation.
- Use `add_subdirectory` to vendor SDL3.
- Link Foundation, Cocoa, and similar frameworks manually only for static builds that fail to propagate them.
- Use `MACOSX_BUNDLE` for a `.app` and embed the SDL3 runtime for distribution.

## Reference

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/fjms9h2hsmjn495m71).
