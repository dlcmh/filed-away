# A `runcc` zsh function for CMake targets

> Based on a DeepSeek conversation about replacing a global npm script with a shell function: [shared conversation](https://chat.deepseek.com/share/9auv17it1ae2xny5y1).

On macOS, the default interactive shell is zsh. A function in `~/.zshrc` can configure, build, and run a CMake target with one command.

## The function

Add this to `~/.zshrc`:

```zsh
runcc() {
    if (( $# != 1 )); then
        print -u2 "usage: runcc <target>"
        return 2
    fi

    cmake -S . -B build &&
    cmake --build build --target "$1" &&
    "./build/$1"
}
```

Then reload the file:

```zsh
source ~/.zshrc
```

From a project root containing `CMakeLists.txt`:

```zsh
runcc dummy
```

This expands to:

```zsh
cmake -S . -B build
cmake --build build --target dummy
./build/dummy
```

## Why the quoting matters

`"$1"` is quoted in both commands. Quoting prevents word splitting and filename expansion if the target name contains spaces or shell metacharacters. A target name should normally be a simple identifier, but quoting is still the correct habit.

The `&&` operators stop the chain when a step fails. If configuration fails, the build is not attempted; if the build fails, the executable is not run. The function also returns the status of the failed command.

The argument check prevents an accidental `runcc` with no target from producing an empty `--target` argument or trying to execute `./build/`.

## Where the binary is written

The final path assumes a single-configuration CMake generator, where the executable is written directly to `build/<target>`. Unix Makefiles and Ninja on macOS normally behave this way.

Multi-configuration generators such as Xcode place the binary under a configuration directory:

```text
build/Debug/dummy
```

For those generators, adapt the function:

```zsh
runcc() {
    cmake -S . -B build &&
    cmake --build build --config Debug --target "$1" &&
    "./build/Debug/$1"
}
```

The target's runtime output name can also differ from its CMake target name. In that case, replace `$1` in the final path with the actual output name.

## Scope and alternatives

The function works from any directory because it uses the current directory as the CMake source. Run it from the project root, or add a check for `CMakeLists.txt` if desired.

A shell function is lighter than a global npm package. It has no runtime dependency beyond CMake and zsh, and its behavior is visible in the shell configuration. A standalone script on `PATH` is another reasonable option when the logic grows beyond a few lines.

If the shell is bash rather than zsh, put the function in the appropriate bash startup file instead. The CMake commands are compatible with bash, but `print -u2` is zsh-specific; use `printf` for the usage message in bash.

## Summary

- Define `runcc` in `~/.zshrc`.
- Quote `$1` and use `&&` to stop on failure.
- Configure with `cmake -S . -B build`.
- Build with `cmake --build build --target "$1"`.
- Run `./build/$1` for single-config generators.
- Adjust the path for Xcode or another multi-config generator.

## Reference

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/9auv17it1ae2xny5y1).
