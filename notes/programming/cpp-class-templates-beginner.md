# A beginner's guide to C++ class templates

> Based on a DeepSeek conversation about C++ templates: [shared conversation](https://chat.deepseek.com/share/eukn6fofgp4ixtqbzm). This note focuses only on class templates.

A class template is a class definition with one or more parameters that the compiler fills in when the class is used. The template itself is a blueprint; it does not become a complete type until it is instantiated with concrete arguments.

## The simplest class template

```cpp
template <typename T>
class Box {
public:
    T value;

    explicit Box(T v) : value(v) {}

    T get() const {
        return value;
    }
};
```

`T` is a type parameter. It stands for a type that will be supplied later. The class body then uses `T` like any other type.

```cpp
Box<int> a(42);
Box<double> b(3.14);
Box<char> c('x');
```

`Box<int>` and `Box<double>` are two distinct types. The compiler generates a separate class for each argument list. That process is called **template instantiation**.

## A second parameter with a default

Class templates can also take non-type parameters, such as compile-time integers:

```cpp
template <typename T, int Scale = 1>
class Scaled {
public:
    T value;

    explicit Scaled(T v) : value(v * Scale) {}

    T get() const {
        return value;
    }
};
```

```cpp
Scaled<int> plain(5);         // Scale = 1
Scaled<int, 1000> milli(5);   // Scale = 1000
Scaled<double, 10> tenth(2.5); // Scale = 10
```

`Scale` is a compile-time constant, not a constructor argument. When the second argument is omitted, the default `1` is used. A parameter with a default must not be followed by a parameter without one.

## Defining member functions outside the class

A member function can be defined inside the class body, as above, or outside it:

```cpp
template <typename T>
T Box<T>::get() const {
    return value;
}
```

The `Box<T>::` prefix is required because the definition belongs to the class template, and `template <typename T>` must appear before it.

## Put class templates in headers

The compiler must see the full definition of a class template when it instantiates it. For that reason, class templates are normally defined entirely in a header:

```cpp
// box.hpp
#pragma once

template <typename T>
class Box {
    // full definition
};
```

Splitting the declaration into a header and the member definitions into a `.cpp` file commonly produces linker errors such as `undefined reference to Box<int>::get()`. The `.cpp` file is compiled separately, and the instantiation in another translation unit cannot see the definition it needs.

## Terminology

- **Class template:** the parameterized definition, such as `Box<T>`.
- **Template instantiation:** a concrete class generated from it, such as `Box<int>`.
- **Generic programming:** the broader practice of writing code that works with many types.
- **Template metaprogramming:** an advanced technique that uses templates to compute values during compilation. It is not required for ordinary class templates.

The terms `typename` and `class` are interchangeable in a template parameter list:

```cpp
template <typename T>  // same meaning
template <class T>     // same meaning
```

## Summary

A class template places a type or compile-time value in angle brackets and uses it throughout the class definition. Writing `Box<int>` asks the compiler to instantiate the template for `int`. Definitions usually belong in headers, and each distinct argument list produces a distinct type.
