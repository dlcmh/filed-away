# Basic C++ classes and member initializer lists

> A DeepSeek lesson on C++ class basics, constructors, access specifiers, and why member initializer lists are preferred to assignment in the constructor body
>
> Source: [shared conversation](https://chat.deepseek.com/share/1s9fexoixpo0qekn1t) on chat.deepseek.com. 2 questions, 2 answers. The source link expires when the conversation is deleted from DeepSeek.
>
> Recovered from the shared-conversation HTML export: tables preserved.

---

## User

Basic C++ class lesson.

---

## DeepSeek

# C++ Classes - Basic Lesson

## 1. What is a Class?

A **class** is a blueprint for creating objects. It bundles **data** (attributes) and **functions** (methods) that operate on that data into a single unit.

```cpp
class ClassName {
    // access specifiers
    // data members
    // member functions
};
```

---

## 2. Your First Class

```cpp
#include <iostream>
using namespace std;

class Dog {
public:                    // accessible from outside
    string name;
    int age;

    void bark() {
        cout << name << " says Woof!" << endl;
    }
};

int main() {
    Dog myDog;             // create an object
    myDog.name = "Rex";
    myDog.age = 3;
    myDog.bark();          // output: Rex says Woof!
    return 0;
}
```

---

## 3. Access Specifiers

| Specifier | Meaning |
| --- | --- |
| `public` | Accessible from anywhere |
| `private` | Accessible only inside the class (default for `class`) |
| `protected` | Accessible in the class and derived classes |

---

## 4. Constructors

A **constructor** is a special function that runs automatically when an object is created. It has the same name as the class and no return type.

```cpp
class Dog {
private:
    string name;
    int age;

public:
    // Constructor
    Dog(string n, int a) {
        name = n;
        age = a;
    }

    // Member function
    void showInfo() {
        cout << name << " is " << age << " years old." << endl;
    }
};

int main() {
    Dog d1("Rex", 3);
    Dog d2("Bella", 5);
    d1.showInfo();   // Rex is 3 years old.
    d2.showInfo();   // Bella is 5 years old.
}
```

### Member Initializer List (preferred style)

```cpp
Dog(string n, int a) : name(n), age(a) { }
```

---

## 5. Getters and Setters (Encapsulation)

Use `private` data + `public` methods to control access:

```cpp
class BankAccount {
private:
    double balance;

public:
    BankAccount(double b) : balance(b) {}

    double getBalance() const { return balance; }   // getter

    void deposit(double amount) {                   // setter-like
        if (amount > 0) balance += amount;
    }
};

int main() {
    BankAccount acc(100.0);
    acc.deposit(50);
    cout << acc.getBalance();   // 150
    // acc.balance = 999;       // ❌ error: private
}
```

---

## 6. Objects and Methods in Action

```cpp
class Rectangle {
private:
    double width, height;

public:
    Rectangle(double w, double h) : width(w), height(h) {}

    double area() const {
        return width * height;
    }

    double perimeter() const {
        return 2 * (width + height);
    }
};

int main() {
    Rectangle r(4, 5);
    cout << "Area: " << r.area() << endl;         // 20
    cout << "Perimeter: " << r.perimeter() << endl; // 18
}
```

---

## 7. The `this` Pointer

`this` refers to the current object. Useful when parameter names match member names:

```cpp
class Point {
    int x, y;
public:
    Point(int x, int y) {
        this->x = x;
        this->y = y;
    }
};
```

---

## 8. Complete Example: A Simple `Student` Class

```cpp
#include <iostream>
#include <string>
using namespace std;

class Student {
private:
    string name;
    int id;
    double gpa;

public:
    // Constructor
    Student(string n, int i, double g) : name(n), id(i), gpa(g) {}

    // Getter methods
    string getName() const { return name; }
    double getGpa() const { return gpa; }

    // Update method
    void setGpa(double newGpa) {
        if (newGpa >= 0.0 && newGpa <= 4.0)
            gpa = newGpa;
    }

    // Display
    void print() const {
        cout << "Student: " << name
             << " | ID: " << id
             << " | GPA: " << gpa << endl;
    }
};

int main() {
    Student s1("Alice", 101, 3.8);
    Student s2("Bob", 102, 3.2);

    s1.print();
    s2.print();

    s1.setGpa(3.9);
    s1.print();

    return 0;
}
```

**Output:**

```text
Student: Alice | ID: 101 | GPA: 3.8
Student: Bob | ID: 102 | GPA: 3.2
Student: Alice | ID: 101 | GPA: 3.9
```

---

## 9. Key Takeaways

- **Class** = blueprint; **object** = instance of a class
- Use `private` data + `public` methods (**encapsulation**)
- **Constructors** initialize objects; use initializer lists
- Mark read-only methods `const` when they don't modify state
- Use `this->` when parameter names shadow members
- Group related data + behavior together

---

## 10. Practice Exercises

1. Create a `Circle` class with a constructor taking a radius. Add `area()` and `circumference()` methods.
2. Create a `Book` class with `title`, `author`, and `pages`. Add a `printInfo()` method.
3. Create a `Counter` class with `increment()`, `decrement()`, and `getValue()` methods. Keep the value private.

Want me to go deeper into **inheritance**, **operator overloading**, or **destructors** next?

---

## User

“Member Initializer List (preferred style)” — preferred to what? Show examples.

---

## DeepSeek

# Member Initializer List — Preferred Over What?

The initializer list is preferred over **assignment inside the constructor body**. Let's compare both styles directly.

---

## Style A: Assignment in the body (not preferred)

```cpp
class Dog {
    string name;
    int age;
public:
    Dog(string n, int a) {
        name = n;   // assignment happens AFTER construction
        age = a;
    }
};
```

## Style B: Member initializer list (preferred)

```cpp
class Dog {
    string name;
    int age;
public:
    Dog(string n, int a) : name(n), age(a) { }   // initialized directly
};
```

Both *look* like they do the same thing. But they don't — here's why the initializer list wins.

---

## Reason 1: `const` and reference members **require** it

`const` members and references **cannot be assigned** after construction — they must be initialized at creation. Style A simply won't compile.

```cpp
class Config {
    const int id;
    int& ref;
public:
    // ❌ ERROR: cannot assign to const / reference in body
    // Config(int i, int& r) { id = i; ref = r; }

    // ✅ Only way — initializer list
    Config(int i, int& r) : id(i), ref(r) { }
};
```

---

## Reason 2: Avoids double work (default-construct then assign)

Without an initializer list, every member is **first default-constructed**, then **assigned** in the body. That's two operations instead of one.

```cpp
class Person {
    string name;      // string is default-constructed (""), then assigned
    vector<int> data; // vector is default-constructed (empty), then assigned
public:
    // Body assignment = construct + assign = wasteful
    Person(const string& n, const vector<int>& d) {
        name = n;    // 1) name already built as ""  2) copy-assigned
        data = d;    // 1) data already built empty  2) copy-assigned
    }
};
```

With the initializer list, each member is built **once, directly** from the argument:

```cpp
Person(const string& n, const vector<int>& d)
    : name(n), data(d) { }   // single construction each — no temporary default object
```

For a `string` this is minor; for a large `vector` or a heavy class it can matter a lot.

---

## Reason 3: Members without a default constructor **must** use it

If a member type has no default constructor, Style A can't work — there's no way to "default construct then assign."

```cpp
class Engine {
public:
    Engine(int hp) { /* ... */ }   // no default constructor!
};

class Car {
    Engine engine;
public:
    // ❌ ERROR: Engine has no default constructor to build first
    // Car(int hp) { engine = Engine(hp); }

    // ✅ Must initialize in the list
    Car(int hp) : engine(hp) { }
};
```

---

## Reason 4: Initialization order is fixed (and the list reveals it)

Members are initialized in **declaration order**, *not* the order written in the list. Writing them in the same order avoids confusion and compiler warnings.

```cpp
class Weird {
    int a;   // initialized FIRST
    int b;   // initialized SECOND
public:
    // List order says b then a, but a is really built first!
    Weird(int x) : b(x), a(b) { }   // ⚠️ a uses b before b is initialized → bug
};
```

Correct version — match the list to declaration order:

```cpp
Weird(int x) : a(x), b(a) { }   // ✅ a built first, then b uses it
```

---

## Side-by-side comparison

```cpp
class Account {
    const int id;          // needs initializer list
    string owner;          // cheaper with list
    double balance;
public:
    // ❌ Won't compile (const id) and does extra work
    // Account(int i, string o, double b) { id = i; owner = o; balance = b; }

    // ✅ Preferred
    Account(int i, string o, double b)
        : id(i), owner(std::move(o)), balance(b) { }
};
```

Note the bonus `std::move(o)` — you can move-construct members in the list, something impossible with body assignment.

---

## When can you *not* use it / when is the body fine?

- You **can** mix: use the list for what you can, then do logic in the body:

```cpp
Account(int i, double b) : id(i), balance(b) {
    if (balance < 0) balance = 0;   // logic belongs in the body
}
```

- For plain `int`/`double` members the performance difference is nil — but the style is still preferred for consistency and for the cases above.

---

## Rule of thumb

> **Initialize in the initializer list; use the constructor body only for logic that can't be an initialization.**

That covers `const`/reference members, non-default-constructible members, avoiding double work, move semantics, and keeping initialization order explicit — all at once.

Want me to show how this plays with **inheritance** (calling base-class constructors in the list)?
