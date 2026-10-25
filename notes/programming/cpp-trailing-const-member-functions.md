# Why a C++ member function ends with const

> Based on a DeepSeek conversation about `std::string str() const`: [shared conversation](https://chat.deepseek.com/share/amn0cb9s6qjz1nsi6q).

In a declaration such as:

```cpp
std::string str() const;
```

the `const` applies to the member function, not to the return type. It promises that calling `str()` will not modify the object on which it is called.

## What the trailing const means

Every non-static member function receives an implicit object argument: `*this`. A trailing `const` makes that object read-only inside the function. The compiler treats `this` as a pointer to a const object, so an attempt to modify a data member fails:

```cpp
class Counter {
public:
    int value() const {
        return value_;
        // value_ = 0;  // error: cannot modify a member in a const function
    }

private:
    int value_ = 0;
};
```

This is enforced at compile time. It has no runtime cost.

## Const objects can call only const members

For instance member functions, a `const` object or a const reference to an object can call only member functions marked `const`:

```cpp
class Grid {
public:
    Grid(int width, int height) : width_(width), height_(height) {}

    std::string str() const { return "grid"; }
    void clear() { /* ... */ }

private:
    int width_;
    int height_;
};

const Grid grid(10, 10);
grid.str();    // fine: str() is const
grid.clear();  // error: clear() is not const
```

Without the trailing `const` on `str()`, the first call would also fail. The compiler cannot assume that a non-const function will leave a read-only object unchanged.

This is why accessors such as `width()`, `height()`, and `str()` are normally marked `const`. They read state; they do not change it.

## What it does not mean

The trailing `const` is often confused with several other uses of the keyword.

### It is not a const return value

```cpp
std::string str() const;
```

The returned `std::string` is not const. The caller receives a normal string value and may modify it. The `const` belongs to the member function and its implicit object.

A leading const would mean something different:

```cpp
const std::string str();   // const return value; rarely useful for a by-value return
```

### It is not a const parameter

```cpp
std::string str(const Grid& grid);
```

That is a free function taking a const reference. It has no trailing `const`, because it is not a member function.

### It does not make the object deeply immutable

A const member function cannot modify non-mutable data members through `this`. It can still:

- modify a `mutable` member;
- modify global or static state;
- call a function that changes external state;
- observe changes made by another thread.

`const` is a compile-time promise about the object, not a synchronization mechanism.

## The mutable exception

A member declared `mutable` can be changed inside a const member function:

```cpp
class CachedValue {
public:
    int get() const {
        ++lookups_;   // allowed because lookups_ is mutable
        return value_;
    }

private:
    int value_ = 42;
    mutable int lookups_ = 0;
};
```

This is used for caches, instrumentation, and other changes that do not alter the object's logical value. It should be used deliberately; a const function that changes observable state through `mutable` can still surprise callers.

## Const overloading

A class can provide both const and non-const versions of the same member function:

```cpp
class Buffer {
public:
    char& at(int index) { return data_[index]; }
    const char& at(int index) const { return data_[index]; }

private:
    std::vector<char> data_;
};
```

A non-const `Buffer` selects the first overload and can modify the element. A const `Buffer` selects the second overload and receives a read-only reference. The trailing `const` participates in overload resolution.

## When to mark a member function const

Mark a member function `const` when it does not change the object's observable state:

- getters such as `width()`, `height()`, and `str()`;
- calculations such as `area()`;
- comparisons and queries;
- functions that only read internal containers.

Do not mark a function const merely because it is short. A mutating operation such as `clear()`, `update()`, or `insert()` remains non-const.

## Relationship to [[nodiscard]]

The two annotations answer different questions:

```cpp
[[nodiscard]] std::string str() const;
```

- `[[nodiscard]]` warns when the caller discards the returned value.
- The trailing `const` promises that the call does not modify the object.

They are complementary. Neither implies the other.

## Summary

A trailing `const` on a member function makes the implicit object read-only for the duration of the call. It allows the function to be called on const objects, prevents accidental mutation of non-mutable members, and participates in const overload resolution. It is a compile-time contract about the object, not about the return value, the arguments, or thread safety.

## Reference

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/amn0cb9s6qjz1nsi6q).
