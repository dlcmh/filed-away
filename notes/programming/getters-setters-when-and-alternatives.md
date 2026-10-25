# Getters and setters: when they help, when they don't, and what to use instead

A getter returns a value from an object. A setter writes a value into it. The advice “make every field private and expose a getter and setter for each one” is common in Java-style code, but it is not a universal design rule.

Encapsulation means that a class controls how its state changes. Private fields with unrestricted setters do not provide that control; they merely replace direct writes with method calls. The useful question is not “does this field have a getter and setter?” but “what rule does this accessor protect, and what interface does the class intend to expose?”

**Scope:** this article targets C++23 or newer. The examples use `std::span`, `std::optional`, and `std::expected` without compatibility shims, and assume that the relevant standard headers are included.

## What accessors are for

Getters and setters are useful when they do at least one of the following:

- enforce an invariant;
- validate input;
- compute a value from the current state;
- hide a representation that may change;
- provide a stable interface for callers;
- avoid copying a large value;
- coordinate a change with other state.

Without one of those purposes, a trivial accessor pair is usually ceremony.

## When a getter is justified

### Hiding representation

```cpp
class Connection {
public:
    bool isOpen() const { return descriptor_ >= 0; }

private:
    int descriptor_ = -1;
};
```

The caller learns whether the connection is open. It does not learn that the implementation uses a file descriptor, nor can it write an arbitrary descriptor into the object.

### Computing a value

```cpp
class Circle {
public:
    explicit Circle(double radius) : radius_(radius) {}

    double radius() const { return radius_; }
    double area() const { return 3.141592653589793 * radius_ * radius_; }

private:
    double radius_;
};
```

`area()` is a getter in the broad sense, but it is not a field accessor. It derives the value from the state. There is no `setArea()`; changing the radius changes the area.

### Exposing an invariant-protected value

```cpp
class BankAccount {
public:
    explicit BankAccount(double initial) : balance_(initial) {
        if (initial < 0.0) {
            throw std::invalid_argument("negative initial balance");
        }
    }

    double balance() const { return balance_; }

    void deposit(double amount) {
        if (amount <= 0.0) {
            throw std::invalid_argument("deposit must be positive");
        }
        balance_ += amount;
    }

    void withdraw(double amount) {
        if (amount <= 0.0 || amount > balance_) {
            throw std::invalid_argument("invalid withdrawal");
        }
        balance_ -= amount;
    }

private:
    double balance_;
};
```

`balance()` is a legitimate read-only getter. The class deliberately has no `setBalance()`, because an arbitrary write would bypass the deposit and withdrawal rules.

### Stable interface

A library can expose `size()`, `empty()`, or `data()` while changing its internal storage. The accessor is part of the interface contract. `std::vector::size()` and `std::string::size()` are familiar examples.

## When a setter is justified

A setter is justified when writing the value requires validation or coordination:

```cpp
class Temperature {
public:
    void setCelsius(double value) {
        if (value < -273.15) {
            throw std::invalid_argument("below absolute zero");
        }
        celsius_ = value;
    }

    double celsius() const { return celsius_; }

private:
    double celsius_;
};
```

The validation is the reason the setter exists. Without it, a public field would be simpler.

Setters can also be justified for notification or synchronization:

```cpp
void setTemperature(double value) {
    temperature_ = value;
    notifyObservers();
}
```

That setter is doing more than assigning a field. The name is still weak, because `setTemperature` hides the notification. A method named `recordTemperature` or `updateTemperature` communicates the side effect more accurately. The best setter is often a method named after the operation, not after the field.

## When not to use accessors

### Passive data

```cpp
struct Point {
    double x;
    double y;
};
```

A `Point` with public coordinates is simple, copyable, and transparent. Adding `getX()`, `setX()`, `getY()`, and `setY()` would add four methods without protecting an invariant.

This is the C++ Core Guidelines distinction: use a `class` when there is an invariant to maintain; use a `struct` when the data members can vary independently.

### Data transfer and configuration objects

A configuration record or a serialized payload is usually a passive data structure. Public fields or aggregate initialization make the code shorter and easier to read.

### Trivial getter/setter pairs

```cpp
class User {
public:
    std::string getName() const { return name_; }
    void setName(std::string name) { name_ = std::move(name); }

private:
    std::string name_;
};
```

If no rule constrains the name, this is a public field with extra steps. The pair does not preserve an invariant; it only changes the syntax of access.

### Exposing an implementation detail

A getter that returns a mutable internal container can be worse than a public field:

```cpp
std::vector<int>& values() { return values_; }
```

The caller can now resize or reorder the internal storage. A read-only view, such as `std::span<const int>`, expresses the intended access level more accurately.

## Alternatives to getter/setter pairs

### Public data and free functions

For passive data, expose the fields and put behavior in free functions:

```cpp
struct Rectangle {
    double width;
    double height;
};

double area(const Rectangle& rectangle) {
    return rectangle.width * rectangle.height;
}
```

This keeps the data type simple and the operation separate.

### Constructor validation and immutable objects

If a value must be valid for its entire lifetime, validate it once in the constructor and provide no setter:

```cpp
class PositiveInteger {
public:
    explicit PositiveInteger(int value) : value_(value) {
        if (value <= 0) {
            throw std::invalid_argument("value must be positive");
        }
    }

    int value() const { return value_; }

private:
    int value_;
};
```

The object is immutable after construction. There is no invalid intermediate state and no setter to misuse.

### Intention-revealing methods

Instead of exposing a field and letting callers implement the operation, expose the operation:

```cpp
account.deposit(100.0);   // not setBalance(balance() + 100.0)
canvas.move(dx, dy);      // not setX(x() + dx)
```

This is the strongest alternative to setters. It keeps the invariant inside the class and gives the operation a name that describes the domain.

### Computed queries

If a value can be derived, provide a query instead of a stored field and a setter:

```cpp
int width() const;
int height() const;
int area() const;   // computed, no setter
```

There is no way for the cached value to disagree with the state, because there is no cached value.

### Read-only views

For collections, return a view rather than a mutable reference or a full copy:

```cpp
std::span<const Vertex> vertices() const { return vertices_; }
```

The caller can inspect the vertices without changing the container. The class controls mutation through its own methods.

### Named factories

If construction can fail, a factory or a validating constructor is clearer than a default-constructed object followed by setters.

A validating constructor can reject invalid arguments by throwing. A factory can return a result type instead:

```cpp
std::expected<Window, std::error_code> createWindow(int width, int height);
```

C++23's `std::expected` reports either a valid `Window` or an error code. `std::optional<Window>` is sufficient when the caller only needs to know that creation failed; `std::expected` is preferable when the reason matters. In both cases, there is no window in a half-initialized state.

## A decision table

| Situation | Prefer |
| --- | --- |
| Passive data record | Public fields or `struct` |
| Field must be validated on write | Private field plus a validating method |
| Value is derived from other state | Computed query, no setter |
| Object should never change | Constructor validation plus read-only getters |
| Caller needs to perform an operation | Intention-revealing method |
| Caller needs read-only access to a container | `std::span<const T>` or a const reference |
| Interface must remain stable across implementations | Accessor methods |
| Change must notify or synchronize | Method named after the operation |

## A practical checklist

1. Does a setter enforce a rule? If not, a public field may be simpler.
2. Does a getter compute, hide representation, or preserve an invariant? If not, consider public data.
3. Can the operation be expressed as behavior instead of assignment? Prefer behavior.
4. Is the type a passive record or an object with a lifecycle? Records favor public data; lifecycle objects favor methods.
5. Would a caller be surprised by a side effect hidden behind `setX`? Rename the method after the side effect.
6. Is the value part of a stable public interface? Accessors are reasonable even when trivial.

## Performance is not the deciding factor

Trivial getters and setters are usually inlined. Public fields are not automatically faster, and accessors are not automatically slower. Virtual accessors and interface-heavy designs can have costs, but those are design decisions to measure, not reasons to expose every field.

## Summary

Getters and setters are tools for protecting invariants, validating input, hiding representation, and defining interfaces. They are not the definition of encapsulation. For passive data, public members are often clearer. For objects with rules, prefer intention-revealing methods and read-only queries over unrestricted setters.

## References

- C++ Core Guidelines, [C.131: Avoid trivial getters and setters](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#c131-avoid-trivial-getters-and-setters).
- C++ Core Guidelines, [C.2: Use `class` if the class has an invariant; use `struct` if the data members can vary independently](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines#c2-use-class-if-the-class-has-an-invariant-use-struct-if-the-data-members-can-vary-independently).
- Martin Fowler, [GetterEradicator](https://martinfowler.com/bliki/GetterEradicator.html).
