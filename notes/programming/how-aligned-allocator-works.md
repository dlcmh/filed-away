# How `AlignedAllocator` works

> Explains the allocator from `tutorial/part-1/01-cpp23-as-a-machine-control-language.md`, which gives a `std::vector<float>` a 64-byte-aligned buffer. Written for a reader who has used `std::vector` but never written an allocator.

The struct is twenty lines long and almost all of it is bookkeeping. There is exactly one idea inside it, and one hardware fact that motivates the idea:

- **The idea:** a `std::vector` never allocates memory itself. It asks a *policy object* — its allocator — for raw memory, then constructs elements into it. Replacing that policy object changes where the memory comes from and how it is aligned.
- **The fact:** a SIMD load such as `vmovaps` requires its address to be aligned to the width of the load. A 16-byte load faults on an address that is not a multiple of 16. A 64-byte-aligned buffer makes 16-, 32-, and 64-byte accesses to the start of the buffer legal, and it matches the cache line size so a buffer does not straddle two lines.

`std::vector`'s default allocation is aligned suitably for the element type — 4 bytes for `float` — and in practice lands on a 16-byte boundary on this platform. That is not enough for 64-byte-wide access, and it is not guaranteed even for 16. Measured on macOS with Apple clang, allocating `std::vector<float>` of several sizes gives:

```
n=  1 addr%64=32
n=  3 addr%64=32
n=  8 addr%64=32
n= 16 addr%64=48
n= 64 addr%64=48
n=257 addr%64=32
```

Every address is 16-byte aligned and none is 64-byte aligned. The allocator turns "usually aligned enough" into a guarantee.

## The one-line summary of the protocol

`std::allocator_traits<A>` defines what a container needs from `A`. It supplies sensible defaults for almost everything — `max_size`, `construct`, `destroy`, `pointer`, `size_type`, and the propagation traits. An allocator therefore has to provide only:

1. `value_type`;
2. `allocate(n)` returning memory for `n` elements, and `deallocate(p, n)`;
3. the ability to be constructed, copied, and compared.

Everything else in `AlignedAllocator` exists because of one of those three, or because of a legacy compatibility rule. Here is the whole struct with the reason for each member:

| Member | Why it exists |
| --- | --- |
| `template <class T, std::size_t Alignment>` | The element type and the alignment are policy parameters, fixed at compile time. |
| `using value_type = T;` | Required; containers name `A::value_type`. |
| `AlignedAllocator() = default;` | Containers default-construct the allocator. Stateless, so there is nothing to do. |
| converting constructor | Required so an allocator for one element type can be built from one for another (used with `rebind`). |
| `allocate` / `deallocate` | The actual work: aligned raw memory in, aligned raw memory out. |
| `rebind<U>::other` | "The same allocation policy, but for element type `U`." |
| `operator==` | Required by the C++20 allocator rules; decides whether one allocator may free another's memory. |

## Line by line

### `template <class T, std::size_t Alignment>`

Two template parameters rather than one because the alignment is part of the policy, not of the element type. `AlignedAllocator<float, 64>` and `AlignedAllocator<float, 32>` are different types, and a vector uses whichever it was instantiated with. Making alignment a compile-time constant lets the compiler see `align_val_t{64}` as a literal.

### `using value_type = T;`

A container has to name the element type it allocates. `std::allocator_traits` reads `A::value_type` and derives `pointer`, `const_pointer`, `size_type`, and `difference_type` from it, which is why the struct does not spell those out.

### The default constructor

```cpp
AlignedAllocator() = default;
```

Nothing to initialise: the type has no data members. That property matters more than it looks, and is discussed under `operator==`.

### The converting constructor

```cpp
template <class U>
explicit AlignedAllocator(
    [[maybe_unused]] const AlignedAllocator<U, Alignment>& other) noexcept {}
```

This allows `AlignedAllocator<double, 64>` to be constructed from `AlignedAllocator<float, 64>`. It is needed because of `rebind`: a container that allocates objects of a second type constructs the rebound allocator from its own. For example, `std::list<T>` allocates nodes, and `std::allocator_traits` may build an allocator for the node type from the one for `T`.

The parameter is unused because the policy carries no state — a stateless allocator constructed from another stateless allocator has nothing to copy. `[[maybe_unused]]` suppresses the warning that would otherwise be produced. Two qualifiers are not decoration:

- `explicit` prevents an implicit conversion between two allocator types in code that did not ask for one. Containers construct explicitly, so nothing is lost.
- `noexcept` is required in practice: containers use allocator construction inside their own `noexcept` move and swap operations. A throwing allocator would either force those operations to lose their `noexcept` guarantee or terminate the program.

### `allocate`

```cpp
T* allocate(std::size_t n) {
    return static_cast<T*>(
        ::operator new(n * sizeof(T), std::align_val_t{Alignment}));
}
```

Four details are worth unpacking.

**`n` is an element count, not a byte count.** The allocator converts it with `n * sizeof(T)`, because the global allocation functions work in bytes. The container computes `n` from its capacity and the element type.

**`::operator new` with a leading `::` is the global allocation function.** Without the `::`, a class-scope `operator new` could be selected instead. This bypasses `new T[n]` on purpose: allocating memory and constructing objects are separate steps, and the container performs the construction through `allocator_traits::construct`.

**The second argument selects the aligned overload.** `std::align_val_t` is a scoped enumeration wrapping `std::size_t`, added in C++17 specifically to disambiguate the over-aligned allocation functions. `operator new(bytes, align_val_t)` returns memory aligned to at least that boundary, or throws `std::bad_alloc`. The plain `operator new(bytes)` guarantees only alignment suitable for any type of default alignment — in practice 8 or 16 bytes — so 64 cannot be requested that way.

**The `static_cast` converts `void*` to `T*`.** Allocation functions return `void*`; the cast is purely a type adjustment and compiles to nothing.

### `deallocate`

```cpp
void deallocate(T* p, std::size_t n) noexcept {
    ::operator delete(p, n * sizeof(T), std::align_val_t{Alignment});
}
```

The rule that matters is that the deallocation must use the same form as the allocation. Mixing `operator new(n)` with `operator delete(p, n, align_val_t)` is undefined behaviour, because the implementation records which allocation function was used and routes the deallocation accordingly. The size is passed again so the compiler can use the *sized* deallocation entry point, which some allocators exploit to skip a lookup.

`deallocate` is marked `noexcept` because allocators are required to be non-throwing here. Freeing memory cannot fail in a recoverable way, so a throw would be a report of a bug, not a condition to handle.

Note what is absent: no check that `n` matches the value originally passed to `allocate`. Passing a different `n` is a contract violation that no implementation is required to detect.

### `rebind`

```cpp
template <class U>
struct rebind {
    using other = AlignedAllocator<U, Alignment>;
};
```

This answers the question "what would the equivalent allocator for `U` be?" — the same alignment policy, applied to a different element type. Node-based containers need it; `std::vector` does not, but `std::allocator_traits` is allowed to instantiate it, so omitting it is a portability risk.

The `Alignment` parameter is carried across unchanged. That is the point: rebinding changes what is allocated, never the policy under which it is allocated.

### `operator==`

```cpp
bool operator==(const AlignedAllocator&) const = default;
```

C++20 lets `= default` synthesize the comparison. Since the class has no members, two instances always compare equal. This is not a technicality. The allocator contract says that memory allocated by one allocator may be deallocated by another only if the two compare equal. For a stateless allocator that is exactly the right answer: any `AlignedAllocator<float, 64>` can free memory obtained from any other, which is what allows a `std::vector` to be moved, swapped, or have its buffer replaced without carrying the original allocator object around.

If the allocator held state — an arena pointer, an alignment chosen at run time, a statistics sink — `operator==` would have to compare that state, and `= default` would do the right thing automatically.

## What `std::allocator_traits` fills in

The struct looks minimal because the traits layer supplies the rest. Given only the members above, `std::allocator_traits<AlignedAllocator<T, A>>` provides:

- `max_size()` — the largest element count that can be requested, derived from the size limits;
- `construct(p, args...)` and `destroy(p)` — placement construction and explicit destructor call;
- `select_on_container_copy_construction()` — a copy of the allocator when a container is copied;
- `propagate_on_container_copy_assignment`, `propagate_on_container_move_assignment`, `propagate_on_container_swap` — all `false_type` by default, which is correct for a stateless allocator;
- `is_always_equal` — true here, because the allocator is an empty type and therefore every instance compares equal.

This is why writing the allocator is mostly ceremony: the standard library implements the contract on top of a small set of hooks, and the hooks here are four functions and a typedef.

## How it is used

```cpp
struct Matrix {
    std::size_t rows = 0;
    std::size_t cols = 0;
    std::vector<float, AlignedAllocator<float, 64>> data;

    Matrix(std::size_t r, std::size_t c)
        : rows(r), cols(c), data(r * c, 0.0F) {}

    [[nodiscard]] float* row(std::size_t i) { return data.data() + i * cols; }
};
```

The allocator is a template argument to the vector type, so it is part of `Matrix`'s type and travels with it. Construction of `data` with `(r * c, 0.0F)` calls `allocate(r * c)`, then constructs each element; destruction calls `deallocate` with the same count. No explicit `delete` appears anywhere, which is the RAII property the tutorial is relying on.

A two-line check confirms the guarantee, and the second allocation happens when the vector grows:

```cpp
std::vector<float, AlignedAllocator<float, 64>> v(1000, 0.0F);
auto base = reinterpret_cast<std::uintptr_t>(v.data());
std::printf("base %% 64 = %zu\n", base % 64);   // prints 0

for (int i = 0; i < 100; ++i) v.push_back(1.0F);
auto grown = reinterpret_cast<std::uintptr_t>(v.data());
std::printf("base %% 64 = %zu\n", grown % 64);  // still 0
```

## What the guarantee covers, and what it does not

The allocator aligns the **start of the buffer**. It says nothing about element addresses inside it, and nothing about the address of an arbitrary row.

`Matrix::row(i)` returns `data.data() + i * cols`, so row `i` begins at an offset of `i * cols * sizeof(float)` bytes. That offset is a multiple of 64 only when `cols` is a multiple of 16 (for `float`): 512 columns give a stride of 2,048 bytes, which is 32 cache lines exactly. With 100 columns the stride is 400 bytes, and row 1 begins 16 bytes into a cache line — the base is still 64-byte aligned, but the row is not. Code that assumes every row start can be loaded with a 64-byte access must therefore either pad the row stride or restrict the matrix order to multiples of 16.

The same reasoning applies to `float` elements: `alignof(float)` is 4, so the compiler would never align a `float` buffer to 64 bytes on its own. The allocator creates a requirement the type system does not express.

## Mistakes worth knowing about

- **Mismatched allocation and deallocation forms.** `operator new(n)` must pair with `operator delete(p)`; `operator new(n, align_val_t{a})` must pair with `operator delete(p, n, align_val_t{a})`. Mixing them is undefined behaviour.
- **Passing a different `n` to `deallocate`.** Nothing checks it, and some implementations rely on it.
- **Forgetting `noexcept` on the allocator operations.** A throwing allocator can turn a vector's move constructor into a terminate call.
- **Giving the allocator state and not comparing it.** If a member is added, `operator==` must compare it, or two allocators that cannot in fact free each other's memory will compare equal.
- **Expecting the allocator to do more than align.** It does not pool allocations, track statistics, or reuse memory. It is a two-function policy, and the standard library does the rest.

## Why write it at all

For most code, the right answer is not to write an allocator: use `std::vector<T>` and let the default allocation handle alignment. This is the case where writing one is justified, because the requirement comes from the instruction set rather than from the program's logic, and the standard library has no way to know that a particular buffer will be consumed by 64-byte loads. The twenty lines are the price of making that requirement part of the type.
