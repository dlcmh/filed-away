# What `do_not_optimize` does, and how to read its inline assembly

> Based on a DeepSeek conversation about the `do_not_optimize` helper in the accelerator tutorial: [shared conversation](https://chat.deepseek.com/share/vfsuy8fmhtm8i3uxh7).

A benchmark can measure an empty loop if the compiler decides that the computed result is unused. At `-O3`, dead-code elimination may remove an entire calculation whose result is never observed.

`do_not_optimize` prevents that:

```cpp
template <class T>
inline void do_not_optimize(T const& value) {
    asm volatile("" : : "r,m"(value) : "memory");
}
```

It emits no machine instructions. It changes what the compiler is allowed to assume.

## Why the helper is needed

Suppose a benchmark computes a result but never prints or stores it:

```cpp
auto result = expensive_kernel(input);
```

If `result` has no observable use, the optimizer can remove the call and the computation. The benchmark then measures the cost of doing nothing.

The helper creates an artificial use:

```cpp
auto result = expensive_kernel(input);
do_not_optimize(result);
```

The compiler must now treat `result` as read by something it cannot inspect. The computation feeding that value must survive.

## Reading the inline assembly

The syntax is GNU extended assembly, supported by GCC and Clang. It is not standard C++.

The general form is:

```text
asm volatile ( "assembly template"
             : output operands
             : input operands
             : clobbers );
```

The helper has empty sections:

```cpp
asm volatile("" : : "r,m"(value) : "memory");
```

| Part | Text | Meaning |
| --- | --- | --- |
| `asm` | `asm` | Start an inline-assembly statement. |
| `volatile` | `volatile` | Do not remove the statement merely because it has no output. |
| Template | `""` | Emit no assembly instructions. |
| Outputs | empty | The statement returns no value. |
| Inputs | `"r,m"(value)` | Read `value`; the compiler may place it in a register or memory. |
| Clobbers | `"memory"` | Assume memory may have been read or written. |

The three colons separate four fields. Two consecutive colons mean that the output field is empty.

### The empty assembly template

```cpp
""
```

is the text that would be copied into the generated assembly. It is empty, so the compiler emits no instruction. The statement exists only to constrain optimization.

### The input constraint

```cpp
"r,m"(value)
```

says that `value` is an input to the assembly statement. The constraint string offers the compiler a choice:

- `r`: a general-purpose register;
- `m`: a memory operand.

The comma means either is acceptable. The compiler chooses the form that fits the surrounding code. Because the template contains no instruction, there is no `%0` placeholder to refer to the operand. The input still matters: the compiler must make the value available as though an instruction could read it.

### The memory clobber

```cpp
"memory"
```

tells the compiler that the assembly statement may read or write arbitrary memory. It acts as a compiler memory barrier: loads and stores cannot be freely moved across it, and cached memory values may need to be reloaded.

This is broader than the input operand itself. The input `value` is read, but the clobber says that the assembly can affect other memory as well. That broad effect is intentional in a benchmark barrier.

### The volatile qualifier

`asm volatile` prevents the compiler from deleting the statement because it has no outputs. Without `volatile`, an empty `asm` statement with no outputs could be treated as dead code.

`volatile` here applies to the assembly statement, not to a C++ variable. It is different from declaring a variable `volatile`.

## Why `r,m` rather than forcing one

Forcing every value into a register would add moves. Forcing every value into memory would require a stack slot and a store. The `"r,m"` constraint lets the compiler choose either form, reducing the barrier's impact on the code being measured.

The helper is generic:

```cpp
template <class T>
inline void do_not_optimize(T const& value);
```

`T const&` accepts a value without copying it. The function template can be used with different result types. `inline` permits the definition to appear in a header without multiple-definition problems; the function template is normally in a header anyway.

## `[[nodiscard]]` is not a substitute

`[[nodiscard]]` and `do_not_optimize` solve different problems.

`[[nodiscard]]` is a diagnostic attribute:

```cpp
[[nodiscard]] int compute();
```

It asks the compiler to warn when a caller ignores the return value. It does not make the result observable, does not force the computation to run, and does not prevent dead-code elimination. A warning can appear and the optimizer can still remove the unused computation.

`do_not_optimize` creates an actual optimization barrier. The compiler believes the value is consumed and that memory may be affected.

`[[nodiscard]]` is useful for catching mistakes. It is not a benchmarking barrier.

## Why clangd may not flag typos in the template body

Template bodies are checked more lazily than ordinary function bodies. Some errors depend on the concrete type substituted for `T`, so they are diagnosed only when the template is instantiated.

clangd may skip full semantic analysis of template bodies in headers for performance. A typo in a dependent context may therefore produce no squiggle until the template is instantiated by a real use. The absence of a warning is not proof that the body is correct. Compiling a test that calls the template is the reliable check.

## Portability

The `asm volatile` form is a GCC/Clang extension. MSVC does not accept this syntax. Benchmark libraries use compiler-specific implementations: GNU-style inline assembly on GCC and Clang, and intrinsics or compiler barriers on MSVC.

The `"memory"` clobber also inhibits some optimizations around the barrier. That is acceptable in a benchmark harness, but it is not something to place in a performance-critical inner loop indiscriminately.

## Summary

```cpp
template <class T>
inline void do_not_optimize(T const& value) {
    asm volatile("" : : "r,m"(value) : "memory");
}
```

- `asm volatile` creates a compiler-visible statement that cannot be deleted.
- `""` emits no machine instructions.
- `"r,m"(value)` tells the compiler that `value` is an input, using a register or memory.
- `"memory"` tells the compiler that memory may change, creating a barrier.
- `[[nodiscard]]` only warns about ignored results; it does not keep computations alive.
- The construct is a GCC/Clang extension and belongs in benchmark instrumentation, not ordinary production code.

## Reference

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/vfsuy8fmhtm8i3uxh7).
