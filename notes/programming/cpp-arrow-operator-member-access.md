# The C++ arrow operator: accessing members through pointers

> Based on a DeepSeek conversation about `->` in C++: [shared conversation](https://chat.deepseek.com/share/e09qr9q1uoc8mx5r8k). This article expands the explanation with examples and context.

In C++, `ptr->member` accesses a member of the object that `ptr` points to. It is shorthand for `(*ptr).member`:

```cpp
ptr->member    // equivalent to (*ptr).member
```

The operator is called the arrow operator, or the member access operator for pointers. It applies to raw pointers and to pointer-like types such as smart pointers and iterators.

For a raw pointer, the equivalence with `(*ptr).member` is exact. For a class type, `ptr->member` invokes the overloaded `operator->`; that case is discussed below.

## Why the arrow exists

A pointer does not contain the members of the object it addresses. To reach a member, the program must first dereference the pointer and then apply the dot operator:

```cpp
Point* ptr = &p;
(*ptr).x = 5;    // dereference, then access x
```

Writing `*ptr.x` does not work because the dot operator binds more tightly than the unary `*`. The expression is parsed as `*(ptr.x)`, not as `(*ptr).x`. The arrow operator removes the need for parentheses and makes the dereference implicit.

## A complete example

```cpp
#include <iostream>

struct Point {
    int x = 0;
    int y = 0;

    void print() const {
        std::cout << x << ", " << y << '\n';
    }
};

int main() {
    Point p{1, 2};
    Point* ptr = &p;

    ptr->x = 5;      // arrow operator
    (*ptr).x = 5;    // equivalent dereference plus dot

    ptr->print();    // call a member function through a pointer
}
```

Both assignment forms modify `p.x`. The arrow form is the conventional one for pointers.

## When to use the arrow

Use `->` when the left-hand side is a pointer or a type that behaves like one. The examples below assume the `Point` type from the previous section and the relevant standard headers.

```cpp
std::unique_ptr<Point> up = std::make_unique<Point>();
up->x = 10;                 // smart pointer

std::vector<Point> v{{1, 2}};
auto it = v.begin();
it->x = 99;                 // iterator
```

The same syntax appears inside member functions through the implicit `this` pointer:

```cpp
struct Counter {
    int value = 0;

    void increment() {
        this->value += 1;
    }
};
```

`this` is a pointer to the current object, so `this->value` is equivalent to `(*this).value`.

## Dot versus arrow

| Expression | Left-hand side | Meaning |
| --- | --- | --- |
| `p.x` | Object or reference | Access a member directly |
| `ptr->x` | Pointer-like object | Access a member through a pointer |
| `(*ptr).x` | Pointer | Dereference explicitly, then access a member |

The distinction is about the type on the left, not about the member being accessed. If the left operand is an object, use `.`. If it is a pointer-like object, use `->`.

## How smart pointers and iterators support the arrow

A class can overload `operator->`:

```cpp
template <typename T>
class MyPtr {
    T* raw;

public:
    explicit MyPtr(T* p) : raw(p) {}

    T* operator->() const {
        return raw;
    }
};

Point p{3, 4};
MyPtr<Point> mp(&p);
mp->x = 7;    // calls MyPtr::operator->, then accesses Point::x
```

This example only demonstrates the member-access syntax. A real owning smart pointer must also manage the lifetime of the object it points to.

For `a->b`, the compiler applies `operator->` repeatedly until the result is a raw pointer, then performs the member access. This chaining is why `std::unique_ptr`, `std::shared_ptr`, and standard iterators work with the same syntax as raw pointers.

An overloaded `operator->` must return a pointer or another object that itself supports `operator->`. Returning a reference to the member directly is not sufficient.

## Common mistakes

- **Null pointers.** The arrow operator does not check whether the pointer is null. Dereferencing a null pointer is undefined behavior, so validate the pointer before use when null is possible.
- **Lifetime.** The arrow operator does not extend the lifetime of the pointed-to object. A pointer to a destroyed object remains invalid even though the syntax is unchanged.
- **Wrong operator for the left operand.** An object uses `.`; a pointer-like object uses `->`. Applying `->` to an object that does not overload `operator->` is a compile-time error.
- **Confusing the arrow with a trailing return type.** In `auto add(int a, int b) -> int`, the `->` introduces the return type; it is not member access. The pointer-to-member operator `ptr->*pm` is a separate operator.

## Summary

`ptr->member` accesses a member through a pointer and is equivalent to `(*ptr).member`. It is the standard form for raw pointers, smart pointers, iterators, and `this`. The operator can be overloaded, which allows pointer-like classes to preserve the same syntax.

## Reference

- cppreference.com, [Member access operators](https://en.cppreference.com/w/cpp/language/operator_member_access).
