# Autorelease pools in metal-cpp: drain versus release

> Based on a DeepSeek conversation about replacing `pool->drain()` with `pool->release()` in an SDL3 and metal-cpp program: [shared conversation](https://chat.deepseek.com/share/0pd80g1rsub6rq1lbs).

The short answer is no. `drain()` is the correct and idiomatic call for an `NS::AutoreleasePool` created with `alloc()->init()`. `release()` has the same reference-counting effect and is not a technical error, but it obscures the intent and is not the method Apple documents for destroying an autorelease pool.

## The code under review

The program creates the pool after the SDL window and Metal device have been created, and drains it at the end of `main`:

```cpp
NS::AutoreleasePool* pool = NS::AutoreleasePool::alloc()->init();

// ... window creation, device creation, event loop ...

device->release();
SDL_DestroyWindow(window);
SDL_Quit();
pool->drain();
```

The pool is created with `alloc` and `init`, so the program owns it. Ownership must be relinquished before the process exits, otherwise the pool object leaks. `drain()` relinquishes that ownership.

## What an autorelease pool does

Cocoa uses reference counting. Objects created with `alloc`, `new`, `copy`, or `mutableCopy` are owned by the creator. Objects returned by convenience methods are often autoreleased: they are placed in the current autorelease pool and receive a release message when that pool is drained.

metal-cpp follows the same object-allocation and reference-counting conventions as Cocoa. Its C++ objects are not eligible for automatic reference counting, so temporary Foundation objects need a defined cleanup point. The autorelease pool provides that point.

| Operation | Ownership effect |
| --- | --- |
| `alloc()->init()` | Creates the pool with a reference count of +1; the caller owns it |
| `autorelease` | Defers a release until the enclosing pool is drained; the caller does not own the object |
| `release` | Decrements the reference count |
| `drain` | Ends the pool; autoreleased objects receive their deferred release |

## Why `drain` is preferred

Apple's documentation recommends `drain` for autorelease pools. For a reference-counted pool, `drain` and `release` have the same effect on the pool itself: the pool is destroyed when its count reaches zero. The difference is semantic. `drain` states that the pool is being emptied and destroyed; `release` states only that a reference count is being decremented.

That distinction matters in review. A reader who sees `pool->release()` must determine whether the call is ordinary reference-count management or the end of the pool's lifetime. A reader who sees `pool->drain()` knows the pool is finished. Since metal-cpp follows Cocoa's conventions, the same naming guidance applies.

Using `release()` does not produce a leak or an incorrect result here. It is a less precise expression of the same operation, and it departs from the documented convention.

Either call relinquishes the pool:

```cpp
pool->drain();    // preferred: ends the pool
pool->release();  // same reference-counting effect; less precise
```

Do not call both. The second call would over-release the pool.

## Cleanup order and early exits

The sample creates the pool after the early returns for SDL initialization, window creation, and Metal device creation. Every path that reaches pool creation therefore also reaches the drain at the end.

A refactor can break that property. If the pool is created before a new early return, the new path must also drain the pool, or the pool must be managed by a scope guard. The cleanup order itself is otherwise conventional: release the explicitly owned Metal resources and SDL objects, then drain the pool that owns the autoreleased Foundation objects.

## Summary

- The pool is owned because it was created with `alloc()->init()`.
- It must be drained or released before the process exits.
- `drain()` is the documented, intention-revealing method for an autorelease pool.
- `release()` works, but it is less idiomatic and less clear in review.
- Ensure that every exit path after pool creation reaches the drain.

## References

- Apple, [Advanced Memory Management Programming Guide: Basic Memory Management Rules](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/MemoryMgmt/Articles/mmRules.html).
- Apple, [`NSAutoreleasePool`](https://developer.apple.com/documentation/foundation/nsautoreleasepool).
- Apple, [`NSAutoreleasePool.drain()`](https://developer.apple.com/documentation/foundation/nsautoreleasepool/drain).
- Apple, [metal-cpp](https://github.com/apple/metal-cpp).
