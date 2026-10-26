# When to use SYSTEM in CMake include directories

> Based on a Gemini conversation, “Understanding SYSTEM in CMake Include Directories”: [shared conversation](https://share.gemini.google/MSSB86QOOa6j).

The `SYSTEM` keyword in `target_include_directories` marks an include directory as containing system or external headers. It does not change how the target is built, and it is not required for compilation. Its main purpose is to suppress compiler warnings that originate in those headers.

```cmake
target_include_directories(chrspaceinvaders SYSTEM PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
```

That use is usually wrong for a project's own headers. The directory contains code maintained by the project, so its warnings are useful.

## What SYSTEM does

With GCC or Clang, CMake translates the marked directory to an `-isystem` include path instead of an ordinary `-I` path. The compiler then treats headers found there as system headers and does not report warnings from them by default.

The primary difference is diagnostics; it does not change linking or the generated binary. Include search order can also differ because `-isystem` directories are searched after ordinary `-I` directories, which matters only when duplicate headers exist. The same program otherwise compiles with or without `SYSTEM`; the visible difference is whether warnings from those headers appear in the build output.

## The usual rule

Use `SYSTEM` for third-party code whose warnings are outside the project's control:

```cmake
target_include_directories(chrspaceinvaders SYSTEM PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party/metal-cpp
)
```

Do not use it for the project's own headers:

```cmake
target_include_directories(chrspaceinvaders PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
)
```

The project's headers should be checked under the same warning flags as the project's source files. Suppressing them hides deprecations, suspicious conversions, unused parameters, and other issues in code that the project can fix.

## Why the distinction matters

A build with many warnings from a third-party dependency becomes noisy. Developers stop reading the output, and genuine warnings in project code are missed. `SYSTEM` is a practical way to keep third-party noise out of the build.

The same mechanism becomes harmful when applied to local headers. A warning in a local header is a warning about local code. Silencing it removes useful feedback from exactly the code the project is responsible for maintaining.

## Scope and propagation

`SYSTEM` is placed after the target name and before the visibility keyword:

```cmake
target_include_directories(<target> SYSTEM PRIVATE <directory>)
```

With `PRIVATE`, the treatment applies to the target's own compilation. With `PUBLIC` or `INTERFACE`, the include directory can propagate to targets that link against it. Marking a public include directory as `SYSTEM` therefore affects consumers as well, which is another reason to reserve it for genuinely external headers.

Imported targets may already carry system include directories. CMake's `NO_SYSTEM_FROM_IMPORTED` target property can disable that behavior when a project needs warnings from an imported target's headers.

## Practical checklist

- Is the header maintained by this project? Do not use `SYSTEM`.
- Is the header from a third-party dependency? `SYSTEM` is reasonable.
- Is the warning suppression hiding a problem the project can fix? Remove `SYSTEM`.
- Is the include directory propagated to other targets? Check whether `PUBLIC` or `INTERFACE` spreads the system treatment.
- Is the build using imported targets? Check whether their interface includes are already treated as system.

## Summary

`SYSTEM` is a warning-control mechanism for external headers. It is not required for a successful build. For `${CMAKE_CURRENT_SOURCE_DIR}/include`, the project's own code, remove it. For vendored or third-party headers, keeping it is the intended use.
