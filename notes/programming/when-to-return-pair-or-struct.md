# When to return a pair and when to define a struct

> Based on a DeepSeek conversation about `std::pair<int, int>` in function declarations: [shared conversation](https://chat.deepseek.com/share/11vrc968sn90eibgcq).

`std::pair<int, int>` bundles two integers into one value. In a function declaration it is usually the return type:

```cpp
#include <utility>

std::pair<int, int> minmax(int a, int b) {
    if (a < b) {
        return {a, b};
    }
    return {b, a};
}
```

The caller can unpack it with structured bindings:

```cpp
auto [low, high] = minmax(5, 3);  // low = 3, high = 5
```

Without structured bindings, the fields are `.first` and `.second`:

```cpp
auto range = minmax(5, 3);
int low = range.first;
int high = range.second;
```

A pair is also valid as a parameter. The output examples assume `<iostream>` is included:

```cpp
void printCoordinates(std::pair<int, int> point) {
    std::cout << point.first << ", " << point.second << '\n';
}
```

## What a pair is good for

Use `std::pair` when the meaning of the two values is obvious from the function or context:

- a coordinate: `(x, y)`;
- a range: `(low, high)`;
- a key and value in generic code;
- a quick two-value return from a small helper.

The standard library uses pairs heavily. A `std::map` element is a `std::pair<const Key, Value>`, because the key and value roles are fixed by the container.

The advantage is that no new type is required. The disadvantage is that the field names carry no meaning.

## When a pair becomes unclear

```cpp
std::pair<int, int> getSize();
```

What does `.first` mean here: width or height? What does `.second` mean? The names are positional, not semantic. A caller must remember the convention or read the implementation.

If the two values represent a specific concept and are used in several places, define a small named type:

```cpp
struct Size {
    int width;
    int height;
};

Size makeSize(int width, int height) {
    return Size{width, height};
}
```

The call site becomes self-documenting:

```cpp
Size size = makeSize(1920, 1080);
std::cout << size.width << " x " << size.height << '\n';
```

Structured bindings still work with the struct:

```cpp
auto [width, height] = size;
```

The field order must still match, but the type name and field declarations make the intended meaning visible.

## A struct can carry behavior

A pair has no domain-specific behavior. A named struct can add methods and operators:

```cpp
struct Size {
    int width;
    int height;

    int area() const {
        return width * height;
    }

    bool operator==(const Size&) const = default;
};
```

Now `area()` is part of the type, and equality compares both fields. A pair cannot express that without free functions or wrappers.

## Passing and returning values

A `Size` containing two `int` members is small. Returning it by value and passing it by value are inexpensive; the compiler can apply return-value optimization.

For a large struct, return by value is still normal, but pass by const reference:

```cpp
BigConfig makeConfig();              // return by value
void apply(const BigConfig& config); // pass large objects by const reference
```

Do not pass a large struct by value merely because it is a struct. The same copy cost applies to a large pair or tuple.

## A decision table

| Situation | Prefer |
| --- | --- |
| Two values with obvious meaning | `std::pair` |
| Two values with domain names, used in several places | Named `struct` |
| More than two related values | Named `struct` |
| A homogeneous list of values | `std::vector` or `std::array` |
| Generic key/value storage | `std::pair` |
| Values with methods or invariants | Named `struct` or `class` |

## Summary

`std::pair<int, int>` is a compact way to return two integers, and structured bindings make it convenient. It is appropriate when the positional meaning is obvious. When the values have names, appear in several places, or need behavior, a small `struct` is clearer and more extensible. The cost of defining the struct is usually lower than the cost of remembering what `.first` and `.second` mean.

## Reference

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/11vrc968sn90eibgcq).
