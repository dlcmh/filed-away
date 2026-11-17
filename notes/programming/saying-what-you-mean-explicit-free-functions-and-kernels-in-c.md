# Saying what you mean: `explicit`, free functions, and why kernels stay in C

> A beginner-friendly walk through four connected questions: why C++ has the `explicit` keyword, why code can live outside classes, why other languages make you write `self` and `impl`, and why operating-system kernels are still written in C.

C++ has a reputation for being strict, so it is surprising that it will silently turn an `int` into a class instance when you did not ask. The keyword `explicit` exists to stop that, and the history of why it was needed explains a lot about the language. The same design choice — trust the programmer, provide an escape hatch when trust was misplaced — explains why C++ lets functions live outside classes, why other languages do not, and why the most privileged code in an operating system is still written in C.

This article takes those threads in order. Each one is understandable on its own, and they converge on a single idea at the end.

## What a constructor is, and the conversion it enables

A **constructor** is the function that runs when an object is created. `std::string s("hi")` calls a constructor that takes a `const char*`. `Box b(10)` calls a constructor that takes an `int`.

A constructor that takes exactly one argument is also, without any extra syntax, a **conversion operator**. It tells the compiler: "anywhere a `Box` is expected, an `int` will do, because I can build one from it." The compiler then performs that conversion silently:

```cpp
class Box {
public:
    Box(int size) { /* ... */ }
};

void printBox(Box b);

int main() {
    printBox(42);   // compiles: 42 becomes Box(42) without being asked
}
```

This is called an **implicit conversion**. It is convenient when the conversion is obvious, such as `double` to `Complex`. It is a defect when the conversion is a guess about intent.

## `explicit` in one example

Marking the constructor `explicit` removes the conversion path:

```cpp
class Box {
public:
    explicit Box(int size);
};

void printBox(Box b);

int main() {
    printBox(42);        // error: no implicit conversion
    printBox(Box(42));   // fine: the conversion is written out
}
```

Nothing else changes. `Box(42)`, `Box b(42);`, and `Box b{42};` all still work. What stops working is every place where the compiler had to invent a `Box` from an `int` on its own.

The standard library uses this for exactly the case beginners find confusing. `std::vector<int> v(10)` is a vector of ten zeros. If the size constructor were not `explicit`, `std::vector<int> v = 10` would look like an assignment of the value 10 and would actually mean "ten empty elements". That sentence is easy to misread, so the constructor is marked and the misreading is a compile error.

## Why C++ allowed this in the first place

The short answer is that implicit construction was a feature before it was a hazard, and changing the default afterwards would have broken existing code.

In the early 1990s, letting the compiler build a `String` from a `char*` or a `Complex` from a `double` removed a great deal of boilerplate. C++ was also designed with close C compatibility, and C converts freely between arithmetic types, so extending that permissiveness to user-defined types fit the spirit of the language.

The problem surfaced inside the standard library itself. The `std::vector` size constructor is the classic example: `std::vector<int> v = 10` reads as an assignment and means something else. A 1995 proposal, N0624, was written specifically to introduce `explicit` so that library authors could opt out of implicit conversion for dangerous constructors.

The obvious follow-up is why `explicit` is not the default. The reason is **backward compatibility**: by the time the keyword existed, a large amount of code depended on single-argument constructors converting implicitly. Making every constructor `explicit` by default would have silently broken that code. The committee is conservative about breaking working programs, so the language kept the permissive default and added an opt-out.

The community has since settled the question in the other direction. The C++ Core Guidelines recommend marking single-argument constructors `explicit` by default (Rule C.46), and most style guides agree. The language's default is historical; the recommended practice is the opposite of the default.

## "Single argument" means "callable with one"

The rule is usually stated as "single-argument constructors", which is imprecise. What matters is whether the constructor can be called with **one value**, because one value is all an implicit conversion has to work with.

```cpp
class Timer {
public:
    Timer(int seconds, bool verbose = false);
};

void start(Timer t);

start(30);   // compiles: 30 becomes Timer(30, false)
```

This constructor is written with two parameters, but the second has a default, so it can be called with one argument. It is therefore an implicit conversion path, and it is exactly the kind that surprises people.

```cpp
explicit Timer(int seconds, bool verbose = false);
// start(30);  now a compile error
```

| Constructor | Implicit conversion possible? | Does `explicit` matter? |
| --- | --- | --- |
| `Box(int)` | Yes | Yes |
| `Box(int, bool = false)` | Yes, the default supplies the second argument | Yes |
| `Box(int, int)` | No | Only for brace-initialization (C++11 and later) |
| Copy constructor `Box(const Box&)` | Copying, not conversion | Rarely; it is a niche technique |

The copy constructor is worth a note because it is single-argument: `Box(const Box&)`. It is not an implicit conversion in the problematic sense — it is how copying works, and copying is essential. Marking it `explicit` is possible and occasionally done to prevent `Box b = otherBox;`, but it is unusual.

C++11 added a second, narrower meaning. `explicit` also blocks **copy-list-initialization**, the form with `= { ... }`:

```cpp
class Pair {
public:
    explicit Pair(int a, int b);
};

Pair p1 = {1, 2};   // error with explicit
Pair p2{1, 2};      // fine: direct initialization
```

This is not about converting one value; it is about whether brace initialization with `=` is allowed. It matters for multi-argument constructors, which otherwise have no conversion path to block.

## How to call an explicit constructor

Once a constructor is `explicit`, the call site has to construct the object rather than let the compiler do it. Three forms work:

```cpp
Timer t(30);
start(t);

start(Timer(30));   // the idiomatic inline form
start(Timer{30});   // brace form, also direct initialization
```

One form does not:

```cpp
start(30);          // error
```

The distinction is between **direct initialization** (`Timer t(30)`, `Timer{30}`) and **copy initialization** (`Timer t = 30`). `explicit` blocks the second, because copy initialization is precisely the context in which an implicit conversion would be performed.

If a codebase ends up writing `Timer(...)` at every call site, that is a signal worth reading: callers wanted the conversion. There are two sensible responses. One is to reconsider whether the conversion is genuinely unsafe. The other, usually better, is to keep the constructor explicit and add a small named function:

```cpp
Timer seconds(int s) { return Timer(s); }

start(seconds(30));
```

This is the pattern `std::chrono` uses: `std::chrono::seconds(30)` is a function-style call that puts the unit in the type and the name. It reads as a conversion, is explicit about the unit, and keeps the constructor from converting anything by accident.

## Free functions: an operation does not have to be a member

The second thread starts with a detail that looks incidental. In the examples above, `start(Timer t)` and `seconds(int s)` are **free functions** — functions declared at namespace scope, outside any class. A beginner coming from Java, Python, or JavaScript may read that as a shortcut or a mistake.

It is a deliberate pattern, and the C++ community's default guidance is the counter-intuitive one: prefer a free function when it will do. Herb Sutter's phrasing, which the guideline literature repeats, is to prefer non-member non-friend functions.

The reasons are concrete:

1. **The function does not need private state.** A free function that works through the public interface is less coupled to the class than a member that could reach inside it. `double length(const Vector&)` only reads `x`, `y`, and `z`; making it a member gains nothing and couples the class to the operation.

2. **You cannot modify the type.** Nobody can add a member to `std::vector`, so the standard library extends containers with free functions that take a pair of iterators (the objects that refer to positions inside a container): `std::find(v.begin(), v.end(), 42)`, `std::sort(v.begin(), v.end())`. A member `v.sort()` would have to be added to every container type; the free version works on any pair of iterators.

3. **Symmetry between operands.** A binary operator written as a member privileges its left operand. `a + b` as a member means "ask `a` to add `b`", and implicit conversions apply to the right operand but not the left. A free `operator+(const Vector&, const Vector&)` treats both sides the same way. This is why arithmetic operators are almost always free functions.

4. **It is an operation, not a property.** `start(timer)` reads as an action applied to a timer; `timer.start()` reads as the timer starting itself. When the operation involves two objects — `bool intersects(const Circle&, const Circle&)`, `transfer(from, to, amount)` — a free function expresses the relationship more accurately.

5. **A minimal class is easier to misuse less.** Members define the core that maintains the object's invariant; convenience operations sit outside. Every member is part of the class's interface forever, so a smaller interface is a smaller commitment.

6. **Customization points.** Free functions participate in **argument-dependent lookup** (ADL): when the compiler sees `swap(a, b)`, it searches not only the current scope but also the namespaces associated with the types of `a` and `b`. That makes a free `swap` in your own namespace the mechanism by which generic code customizes behaviour for your type. The same mechanism is why `begin(x)` and `end(x)` are free functions, and why range-based `for` works on user-defined types.

The guidance is not a rule that members are bad. Members are the right choice when the function needs private state, must maintain an invariant, is virtual, or is genuinely the object's own behaviour. `std::string::size()` is a member for a reason.

## Why Python, Ruby, JavaScript, and Swift do not teach this

The free-function pattern is not portable advice. It exists in C++ because of four properties that the other languages do not combine.

**Overloadable operators.** Once `a + b` can be a function rather than a method, the question "where does behaviour live?" has a second answer, and the symmetry argument makes the free answer the better one. Python can overload `__add__`, but that is a method, so the left operand is privileged and `__radd__` exists to patch the asymmetry.

**Generic algorithms.** `std::sort` works on any iterator pair. It cannot be a member, because the container is not part of its signature. C++ built `<algorithm>` around this observation.

**ADL.** No other language in that list has argument-dependent lookup. Swift's extensions are the nearest equivalent, but an extension attaches the method to the type; ADL lets the function float free and still be found.

**Namespaces as the unit of organisation.** A C++ namespace can be reopened and merged across headers, which is how `std::` spans dozens of files and remains one namespace. Python's modules are files; Ruby's modules are mixins; Swift's modules are build units.

The consequence is cultural as much as technical. In Python, "explicit is better than implicit" pushes behaviour into methods and `self` onto every line. In Ruby, everything is a method on an object — even `1 + 2` is `1.+(2)`. In JavaScript, objects are bags of behaviour and `this` is dynamically bound. In Swift, extensions are the sanctioned way to add behaviour, so `v.length()` is the natural form and `length(v)` is not.

## The tree traversal example

The difference is easiest to see in a data structure that attracts many operations. A Python tree-walking class typically grows like this:

```python
class TreeNode:
    def __init__(self, val):
        self.val = val
        self.left = None
        self.right = None

    def inorder(self):
        result = []
        self._inorder_helper(result)
        return result

    def _inorder_helper(self, result):
        if self.left:
            self.left._inorder_helper(result)
        result.append(self.val)
        if self.right:
            self.right._inorder_helper(result)
```

Every traversal added to the class makes the class larger. `self` appears on every line. The helper method exists only to carry the accumulator through the recursion, because the public method cannot take an extra parameter without exposing it. Adding preorder, postorder, level order, height, and a balance check produces a class whose main job is holding algorithms.

The C++ version separates the data from the operations:

```cpp
struct TreeNode {
    int val;
    TreeNode* left = nullptr;
    TreeNode* right = nullptr;
};

void inorder(TreeNode* node, std::vector<int>& out) {
    if (!node) return;
    inorder(node->left, out);
    out.push_back(node->val);
    inorder(node->right, out);
}

std::vector<int> inorder(TreeNode* node) {
    std::vector<int> out;
    inorder(node, out);
    return out;
}
```

`TreeNode` stays small, and each traversal is a function with as many parameters as it needs. The structural point is that traversal is an operation *on* a tree, not a behaviour *of* a node. The Python version blurs that distinction because the class is the only convenient place to put behaviour; the C++ version does not.

None of this is unavailable in Python. Module-level functions taking a node are legal and produce nearly the same shape:

```python
def inorder(node):
    if node is None:
        return []
    return inorder(node.left) + [node.val] + inorder(node.right)
```

The difference is that Python's culture and syntax do not point there, so most code does not do it.

## What `self` and `this` are doing

The keyword that most visibly separates the languages is the receiver. C++ has `this`, but it is almost never written:

```cpp
class Timer {
    unsigned seconds_;
public:
    void reset() { seconds_ = 0; }   // no this->
};
```

The member function already knows which object it was called on, so `this` carries no information the compiler lacks. Conventions such as a trailing underscore on member names exist to avoid the one case where a parameter shadows a member, which is the only time `this->` is needed.

The other languages require the receiver because in each of them it carries information:

- **Python**: `self` is an ordinary parameter. A method is a function with the instance passed as its first argument, so the parameter has to be written.
- **Rust**: `&self`, `&mut self`, and `self` distinguish borrowing from moving. The form of the receiver is what tells the compiler whether the call may mutate the object, so it is load-bearing syntax.
- **JavaScript**: `this` is bound at call time, which is why methods lose it when passed as callbacks and why arrow functions and `.bind()` exist.

C++'s `this` is a plain pointer to the current object with no ownership or binding semantics attached, so omitting it is safe. The verbosity in the other languages is the price of information; in C++ there is nothing to pay for.

## Ceremony, `impl`, and autocompletion

The same reasoning explains the reaction that C++ feels lighter than Rust despite doing more. Rust separates data from behaviour by design: a `struct` declares the fields, and every method lives in an `impl` block and is introduced by `fn`:

```rust
struct Timer { seconds: u32 }

impl Timer {
    fn new(seconds: u32) -> Self { Timer { seconds } }
    fn start(&self) { /* ... */ }
}
```

C++ puts the methods in the class body, and the class body is the scope:

```cpp
class Timer {
public:
    explicit Timer(unsigned seconds) : seconds_(seconds) {}
    void start() { /* ... */ }
private:
    unsigned seconds_;
};
```

Neither choice is free. Rust's separation makes traits (its interfaces) compose predictably and allows a method to be added to any type the program owns, which addresses a real C++ limitation: you cannot add a member function to a type you do not own. C++'s compactness costs it that, and gains a smaller surface at every declaration.

There is a third dimension: what the tooling can know. In Python 2 and early Python 3, an editor could not complete `data.` inside `def process(data):` because nothing recorded what `data` was. Duck typing means a call succeeds if the object happens to have the needed methods, and no tool can enumerate those methods without knowing the type. PEP 484, added in Python 3.5 in 2015, introduced optional type hints, and modern analysers (mypy, Pyright, Pylance) do well when the hints are present. The hints are optional and not enforced at run time, so the result is best-effort inference rather than guaranteed knowledge.

C++ has the same problem in one specific place: templates. Inside `template <typename T> void process(T data)`, `data.` is no better known than in Python until the template is instantiated. C++20 **concepts** were added to declare the required interface, which is what allows an editor to complete members and what produces readable errors instead of pages of instantiation notes.

|  | Type knowledge | Tooling quality | Ceremony cost |
| --- | --- | --- | --- |
| Python, unhinted | None | Poor | None |
| Python, hinted | Optional, unenforced | Good, best effort | Moderate |
| C++, declared types | Enforced | Exact | High |
| C++, unconstrained template | Deferred | Poor without concepts | High |
| Rust | Enforced and inferred | Excellent | Moderate |

## Where C++ belongs in an operating system

The last thread is a common misunderstanding: that Huawei built HarmonyOS in C++ from top to bottom, doing what Linus Torvalds refused to do with Linux.

Huawei did not. HarmonyOS is a multi-language system. The application-facing languages are ArkTS and Cangjie; C and C++ are positioned for native libraries and high-performance modules — game engines, physics, audio and video codecs, and reuse of existing C/C++ code through the NDK.

The kernel is not written in C++. It is a **microkernel** — a kernel that provides only the essentials, such as scheduling and inter-process communication, and leaves device drivers and services to user space — and it is a C codebase, with LiteOS used on lightweight devices. Sources disagree on the language list for the wider system, and some pages mention C, C++, Cangjie, and Rust, but that describes the platform rather than the core kernel.

The tooling around C++ is real, and it is what makes user-space C++ tractable:

- a dedicated NDK toolchain using the BiSheng compiler and the libc++ standard library from LLVM;
- deliberate **ABI isolation** — the ABI being the binary interface between separately compiled components — keeping the system `libc++.so` and the application `libc++_shared.so` in separate namespaces and forcing isolation through C interfaces, so a mismatched standard library cannot crash the system;
- static analysis through CodeArts Check, with Huawei's C/C++ rule sets built in.

Torvalds' 2004 objection was about semantics rather than tooling. He argued on the kernel mailing list that C++ exception handling and hidden memory allocation are unusable in a kernel, and that the compilers of the time could not be trusted. The argument still holds for kernel work: unwinding through destructors inside an interrupt handler or a panic path produces states the kernel cannot recover from, and implicit allocation breaks the requirement that memory use be deterministic and lock-aware. Neither problem is solved by a linter. The only viable C++ for a kernel is one with exceptions, RTTI (run-time type information), and most of the library removed, at which point it is close to C with classes.

The comparison with Android and iOS shows that all three systems made the same choice:

|  | Kernel language | Where C++ lives | Primary application language |
| --- | --- | --- | --- |
| Android | C (Linux kernel) | Native libraries, runtime, some system services | Java, Kotlin |
| iOS | C and assembly (XNU) | Runtime libraries, mixed into Objective-C++ where needed | Objective-C, Swift |
| HarmonyOS | C (microkernel, LiteOS on small devices) | High-performance user-mode modules | ArkTS, Cangjie |

The pattern is identical: C owns the kernel, and C++ is a performance tool for user space. Keeping the most dangerous language features out of the most privileged code is not a Huawei innovation; it is the standard arrangement, and HarmonyOS documents it more explicitly than the others.

## The philosophy underneath: specification is a cost

Four separate observations now line up:

- `explicit` exists so that a dangerous default can be turned off at the point where it is dangerous.
- Free functions exist so that behaviour can live where it belongs rather than inside a class by default.
- Omitting `self` and `this` works because the keyword carries no information in C++.
- Kernels stay in C because the guarantees C++ adds cost more than they are worth in that layer.

The organising idea is that specification is a cost, and its value depends on the layer. A kernel needs deterministic memory behaviour and no unwinding, so the specification is heavy and the language is restricted. A prototype needs iteration speed, so Python is the right tool. A performance-critical user-space module needs compact expression and control, so C++ is the right tool. A user interface needs ergonomics, so ArkTS is the right tool.

An analogy from the conversation captures the feel: C++ is compact and context-dependent, in the way that a dense natural language is, while Rust is verbose and enforced, in the way that legal drafting is. The analogy holds on compactness, on context sensitivity (overload resolution and template deduction depend on the surrounding types), and on where the guardrails sit.

It breaks on one point, and the point matters. C++'s guardrails are not absent; they are deferred. Undefined behaviour, implicit conversions, and silent overloads are rules enforced at run time, by discipline, or not at all. The "stuff just happens" is sometimes "stuff goes silently wrong". Rust's verbosity is the safety: the borrow checker and the explicit bounds prevent entire classes of defect before the program runs.

The reason this matters for the layered view is that reactive correction only works when the failure is detected early and cheaply. A silent defect in a prototype is discovered the next day; a silent defect in a kernel may be discovered by a shipped device. That is why Huawei's C coding standards are paranoid in exactly the ways a kernel needs — mandatory pointer initialisation, integer overflow checks, strict constructor rules, memory allocation validation — despite the language being "minimal". The minimalism is paid for by heavy detection tooling.

That is the defensible version of the philosophy: specify where the specification buys the most, and treat the ability to detect a failure as the precondition for leaving specification out. `explicit` is C++ admitting that one such place needed a guardrail, and the fact that a keyword was required is the argument that defaults are historical decisions rather than moral ones.

## Sources

The C++ material follows the language rules as described in the C++ Core Guidelines and the `std::chrono` and `std::vector` interfaces. The operating-system comparison follows Huawei's HarmonyOS developer documentation, Apple's and Google's platform documentation, and the Linux kernel mailing list thread from January 2004:

- [Linus Torvalds on C++ in the Linux kernel, January 2004](https://lkml.org/lkml/2004/1/20/20)
- [HarmonyOS programming language documentation](https://developer.huawei.com/consumer/cn/doc/guidebook/programming-language1-0000002593254720)
- [HarmonyOS NDK development overview](https://developer.huawei.com/consumer/cn/doc/doccenter-capabilities/ndk-development-overview)
- [Huawei C/C++ coding standard for stability](https://developer.huawei.com/consumer/cn/doc/best-practices-V14/bpta-stability-coding-standard-cpp-V14)
- [C++ Core Guidelines, rule C.46](https://rules.sonarsource.com/cpp/tag/cppcoreguidelines/rspec-1709/)
