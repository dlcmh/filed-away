# Autorelease pool lifetime in metal-cpp: keep it wide, use RAII

> A follow-up to [Autorelease pools in metal-cpp: drain versus release](metal-cpp-autorelease-pool-drain-vs-release.md), based on a DeepSeek conversation: [shared conversation](https://chat.deepseek.com/share/0pd80g1rsub6rq1lbs).

A natural question after adding an `NS::AutoreleasePool` to a metal-cpp program is whether the pool should be created after `SDL_Metal_CreateView`, so that a failed view creation can return without draining the pool. The placement should remain before the view call. The repetitive cleanup is better addressed with RAII than by shortening the pool's lifetime.

## Why the pool must come first

`SDL_Metal_CreateView` creates Cocoa objects, including an `NSView` and a `CAMetalLayer`. Those objects may be autoreleased. An autorelease pool must already be active when such an object is created, otherwise the object is added to an outer pool or has no defined cleanup point in the program.

Keeping the pool before the view call gives a simple lifetime rule: the pool covers every Cocoa and metal-cpp operation that follows it. Moving the pool after the view call makes that rule conditional and harder to verify, especially when the initialization sequence grows.

## The failure-path argument

If `SDL_Metal_CreateView` fails and the process returns immediately, skipping `pool->drain()` is harmless in practice because the process is terminating. That is not a sound design rule. Cleanup should not depend on the process ending immediately after the failure, because the same code may later run inside a library, a test harness, or a longer-lived application. A missing drain then becomes a leak.

The correct response to repeated cleanup branches is not to move the pool later. It is to make the pool's lifetime automatic.

## A scope guard for the pool

Define a small non-copyable guard after the metal-cpp and Foundation includes:

```cpp
struct AutoreleasePoolScope {
    NS::AutoreleasePool* pool = NS::AutoreleasePool::alloc()->init();

    ~AutoreleasePoolScope() {
        if (pool) {
            pool->drain();
        }
    }

    AutoreleasePoolScope(const AutoreleasePoolScope&) = delete;
    AutoreleasePoolScope& operator=(const AutoreleasePoolScope&) = delete;
};
```

The constructor creates the pool and the destructor drains it. Deleting the copy operations prevents two guards from owning and draining the same pool.

Create one guard at the start of `main`:

```cpp
int main(int, char**) {
    AutoreleasePoolScope pool;

    // Initialization, including early returns.
    // The pool drains on every exit path.
}
```

The guard is declared before the objects whose autoreleased temporaries it should cover. Because local objects are destroyed in reverse order of declaration, those objects are destroyed before the pool, and the pool is drained last.

## Per-frame pools

The same type can scope a pool to one iteration of the event loop:

```cpp
while (running) {
    AutoreleasePoolScope framePool;

    // Poll events and render.
}
```

The frame pool drains at the end of each iteration, including when the loop exits through `break`. This keeps temporary Foundation objects from accumulating across frames.

A per-frame pool introduces a lifetime constraint: an autoreleased object must not be retained beyond the iteration in which it was created. If a pointer to such an object is stored for later use, the object may be destroyed when the frame pool drains. Objects that must outlive the frame need explicit ownership, not an autoreleased pointer.

## Summary

- Create the pool before `SDL_Metal_CreateView`, not after it.
- Do not rely on process termination to replace cleanup.
- Use a non-copyable scope guard to drain the pool on every return path.
- Declare the guard before the objects it covers.
- Use a per-frame guard for temporary objects, but do not retain those objects past the iteration.
