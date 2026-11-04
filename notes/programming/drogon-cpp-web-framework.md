# Drogon: a C++ web framework for existing C++ systems

> Based on two DeepSeek conversations about [C++ coroutines and Drogon](https://chat.deepseek.com/share/bcr7bbmds3yz60te69) and [why a C++ web framework is useful](https://chat.deepseek.com/share/44z0900bx5h69o37ls).

Drogon is a C++ web framework built on a non-blocking event loop. It supports HTTP, WebSocket, database access, templates, sessions, filters, and a command-line scaffolding tool. It compiles to a native binary and does not require a language runtime such as the JVM, Node.js, or Python.

It is not the default choice for a typical web application. It is useful when the application already has substantial C++ code, when latency and memory overhead matter, or when the service must run as a single native binary on a constrained system.

## Why use a C++ web framework?

Most new web backends are written in Go, TypeScript, Python, or Rust. A C++ framework is a narrower choice, but it has concrete advantages:

- **Existing C++ code can be exposed directly.** A service can call an in-process C++ library instead of adding another process boundary and serialization layer.
- **Low runtime overhead.** There is no managed runtime, interpreter, or virtual machine.
- **A single deployable binary.** This is useful for appliances, edge devices, embedded systems, and small containers.
- **Asynchronous I/O.** Drogon uses `trantor`, its event-loop library, for non-blocking network and database operations.
- **Batteries included.** The framework provides an ORM for PostgreSQL, MySQL, and SQLite, Redis support, sessions, cookies, CSP templates, filters, plugins, and `drogon_ctl`.

The tradeoffs are equally concrete. C++ compilation is slower, object lifetimes and asynchronous callback chains require care, the middleware ecosystem is smaller, and fewer engineers have production experience with modern C++ web services. For a typical CRUD application, Go or TypeScript will usually be faster to build and operate.

## Coroutines and the missing runtime

C++20 introduced coroutines as a language mechanism. A coroutine can suspend and resume, and it is recognized by `co_await`, `co_yield`, or `co_return`. The standard does not provide a scheduler, thread pool, or event loop.

That is the gap Drogon fills. Its event loop and asynchronous infrastructure provide the runtime around the coroutine mechanism. Drogon has supported coroutines since version 1.4, and many blocking or callback APIs have coroutine counterparts with a `Coro` suffix. For example, a synchronous database call such as `execSqlSync()` has a coroutine form such as `execSqlCoro()`.

A coroutine handler uses Drogon's `Task<>` return type rather than `void`. The handler can `co_await` a database result and `co_return` an HTTP response, which keeps the code close to the synchronous form while remaining asynchronous.

This is not free. Drogon's documentation has reported a performance cost of roughly 8% for returning a response through `co_return` compared with the callback form. The coroutine form is usually clearer, but a latency-sensitive service should measure the difference rather than assume it is zero.

Drogon does not make C++ concurrency equivalent to Go's runtime or Node's event loop. It provides a framework-level runtime for a language mechanism that otherwise leaves scheduling to the programmer.

## A minimal Drogon program

The smallest Drogon entry point loads a configuration file and runs the application:

```cpp
#include <drogon/drogon.h>

int main() {
    drogon::app().loadConfigFile("./config.json").run();
    return 0;
}
```

Routes and handlers are then registered through the application object or through controller classes. The configuration file controls listeners, threads, database clients, and logging.

## Getting started on macOS

Homebrew provides a prebuilt Drogon package for Apple Silicon:

```bash
brew install drogon
drogon_ctl version
```

`drogon_ctl` is the framework's scaffolding tool. It is the closest equivalent to a project generator in other ecosystems:

```bash
drogon_ctl create project my_first_app
cd my_first_app
cd build
cmake ..
make
./my_first_app
```

The generated project contains a `controllers/` directory, a `main.cc`, and a `CMakeLists.txt`. After starting the server, visit `http://localhost`. A default page or a 404 response indicates that the server is running and no route has been configured yet.

Drogon examples assume familiarity with C++ classes, lambdas, and smart pointers. Installation is straightforward; reading framework code is easier after those fundamentals are in place.

## Deployment

A Drogon application is a compiled server process, so it does not deploy like a Node.js project.

Vercel can run a Drogon application through its container runtime, but the application is treated as a serverless function. That model introduces cold starts, statelessness, restricted persistent storage, and limitations for long-lived WebSocket connections. The process must also listen on the port supplied by the platform rather than a hard-coded port.

A platform that supports Docker or SSH is usually a better fit:

- a small VPS running the binary under `systemd`;
- a container host with a persistent process;
- a free or low-cost service that permits Docker or shell access.

For a beginner, the important distinction is between a serverless function and a long-running server. Drogon is designed for the latter.

## Interactivity with htmx

Drogon can serve HTML fragments, which makes it compatible with htmx. The browser sends requests through `hx-` attributes, and Drogon returns an HTML fragment that htmx inserts into the page. This avoids a full JavaScript framework while keeping the application interactive.

The combination is sometimes called a hypermedia-driven application. The server remains responsible for application logic and HTML rendering; htmx handles the browser-side request and DOM update. The `HDA_with_Cpp` project is a public example that uses Drogon, htmx, Bootstrap, and SQLite.

## Summary

Drogon is a capable C++ web framework with asynchronous I/O, coroutine support, an ORM, and a native-binary deployment model. It is a poor default for ordinary CRUD services, but a reasonable choice when C++ is already the system language or when runtime overhead and deployment size are central constraints.

Its coroutine support supplies the runtime that bare C++20 does not. That makes asynchronous handlers easier to write, at the cost of C++ complexity and a measurable performance tradeoff in some paths.

## References

- DeepSeek, [C++ coroutines and Drogon](https://chat.deepseek.com/share/bcr7bbmds3yz60te69).
- DeepSeek, [why use a C++ web framework](https://chat.deepseek.com/share/44z0900bx5h69o37ls).
