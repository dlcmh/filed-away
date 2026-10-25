# When to use a newline instead of std::endl in C++

> Based on a DeepSeek conversation about `'\n'` versus `std::endl` in C++: [shared conversation](https://chat.deepseek.com/share/czhgxafw2vgticxv3o).

`'\n'` appends a newline character. `std::endl` appends a newline and flushes the stream. The difference matters because flushing forces buffered output to the underlying device immediately, and that cost is paid on every call.

```cpp
std::cout << "Cleaning up and exiting..." << '\n';    // newline only
std::cout << "Cleaning up and exiting..." << std::endl; // newline + flush
```

`std::endl` is equivalent to `'\n'` followed by `std::flush`. It is not a more correct way to end a line; it is a deliberate request to flush.

## Why flushing is usually unnecessary

`std::cout` is buffered. Characters accumulate in a buffer and are written in larger blocks. This amortizes the cost of the underlying write. Flushing after every line defeats that batching, and flushing inside a loop can be substantially slower than allowing the buffer to fill:

```cpp
for (int i = 0; i < 1'000'000; ++i) {
    std::cout << i << '\n';   // buffered
}
```

Replacing `'\n'` with `std::endl` in that loop requests one million flushes.

## When a flush is justified

Use `std::endl` or an explicit `std::flush` when output must be visible before the program continues:

- An interactive prompt that must appear before blocking for input. In practice, `std::cin` is tied to `std::cout` by default, and formatted input flushes `std::cout` automatically. The flush is often redundant, but it is defensible when input comes from another source.
- Progress output or diagnostics that must be visible immediately.
- Output that must survive an abnormal termination. Normal `return` from `main` and `std::exit` flush the standard streams; `std::_Exit`, `std::quick_exit`, and `abort` do not.
- Coordination with another writer of the same file or device, where ordering must be visible.
- Log-style output where the order of records is more important than throughput.

Outside those cases, `'\n'` is the better default.

## The cleanup message

```cpp
std::cout << "Cleaning up and exiting..." << '\n';
```

At the end of `main`, this is sufficient. A normal return from `main` runs the standard cleanup, which flushes `std::cout`. Adding `std::endl` would request a flush that happens moments later during normal termination anyway.

## Rule of thumb

- Use `'\n'` unless immediate output is required.
- Use `std::endl` or `std::flush` at interactive boundaries, crash-sensitive output, or points where another writer must observe the data.
- Do not use `std::endl` as a habitual line terminator in loops or bulk output.
