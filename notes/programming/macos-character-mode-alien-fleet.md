# A macOS character-mode alien fleet in idiomatic C++

> Based on a DeepSeek conversation about a character-grid Space Invaders sketch: [shared conversation](https://chat.deepseek.com/share/cgxm9z20u1lmqynire). The `GameLoop` class follows the fixed-timestep structure in [`chrspaceinvaders/main.cpp`](https://github.com/dlcmh/cppgamearch/blob/main/src/apps/chrspaceinvaders/main.cpp). This tutorial is a complete, tested macOS version of one part: rows of aliens moving across a terminal.

The earlier character-mode sketch is not a runnable program. It shows a useful idea, but it omits the surrounding program, and character-mode tutorials often rely on Windows-only facilities such as `conio.h`, `windows.h`, or `system("cls")`. Those do not compile on macOS.

The program below uses only standard C++ and ANSI terminal control, both of which work in macOS Terminal. It does not implement a game. It implements a fleet that moves left and right, drops one row when a column reaches the side, and resets when the fleet reaches the bottom.

## What the program does

- A 40 by 20 character canvas is drawn with a border.
- Three rows of six aliens move one column per fixed update.
- When the rightmost or leftmost alien reaches the inner edge, the fleet reverses direction and moves down one row.
- The fleet resets to the top when its lowest row reaches the bottom of the canvas.
- `Ctrl+C` exits the program.

The motion policy is the part worth studying. Rendering, timing, and terminal control are separate from it.

## Design

The program has four classes and a small `main`:

- `Canvas` owns a two-dimensional character buffer. It handles clearing, borders, writing glyphs, and converting the buffer to a string. It knows nothing about aliens, timing, or terminals.
- `Fleet` owns the alien positions and the horizontal direction. It computes the fleet's horizontal bounds, reverses and drops at an edge, and resets when needed. It knows nothing about the terminal or the frame clock.
- `Terminal` owns ANSI escape sequences. It clears the screen once and redraws the canvas from the home position each frame. It knows nothing about alien logic.
- `GameLoop` owns the frame clock and the demo reset policy. It accumulates elapsed time, runs fixed updates, renders once per display frame, and limits the render rate. It does not implement the fleet's horizontal movement rules.
- `main` constructs the objects and starts the loop.

The query methods are marked `[[nodiscard]]`: `width()`, `height()`, `bottom()`, `str()`, and the private `horizontalBounds()`. Discarding their return values is almost always a mistake, and the attribute lets the compiler point it out. It has no runtime cost and addresses clang-tidy's `modernize-use-nodiscard` warning.

## The complete program

Save this as `alien_fleet.cpp`.

```cpp
#include <algorithm>
#include <chrono>
#include <cstddef>
#include <iostream>
#include <string>
#include <thread>
#include <utility>
#include <vector>

class Canvas {
public:
    Canvas(int width, int height)
        : width_(width), height_(height),
          cells_(static_cast<std::size_t>(width * height), ' ') {}

    [[nodiscard]] int width() const { return width_; }
    [[nodiscard]] int height() const { return height_; }

    void clear() {
        std::ranges::fill(cells_, ' ');
    }

    void drawBorder() {
        for (int x = 0; x < width_; ++x) {
            set(x, 0, '#');
            set(x, height_ - 1, '#');
        }
        for (int y = 0; y < height_; ++y) {
            set(0, y, '#');
            set(width_ - 1, y, '#');
        }
    }

    void set(int x, int y, char glyph) {
        if (x < 0 || x >= width_ || y < 0 || y >= height_) {
            return;
        }
        cells_[static_cast<std::size_t>(y * width_ + x)] = glyph;
    }

    [[nodiscard]] std::string str() const {
        std::string out;
        out.reserve(static_cast<std::size_t>((width_ + 1) * height_));
        for (int y = 0; y < height_; ++y) {
            out.append(&cells_[static_cast<std::size_t>(y * width_)],
                       static_cast<std::size_t>(width_));
            out.push_back('\n');
        }
        return out;
    }

private:
    int width_;
    int height_;
    std::vector<char> cells_;
};

class Fleet {
public:
    Fleet(int rows, int columns, int startX, int startY, int fieldWidth)
        : rows_(rows), columns_(columns), startX_(startX), startY_(startY),
          fieldWidth_(fieldWidth) {
        reset();
    }

    void update() {
        const auto [minX, maxX] = horizontalBounds();
        const bool atRightEdge = direction_ > 0 && maxX >= fieldWidth_ - 2;
        const bool atLeftEdge = direction_ < 0 && minX <= 1;

        if (atRightEdge || atLeftEdge) {
            direction_ = -direction_;
            for (auto& alien : aliens_) {
                ++alien.y;
            }
        } else {
            for (auto& alien : aliens_) {
                alien.x += direction_;
            }
        }
    }

    void draw(Canvas& canvas) const {
        for (const auto& alien : aliens_) {
            canvas.set(alien.x, alien.y, 'A');
        }
    }

    [[nodiscard]] int bottom() const {
        int maxY = 0;
        for (const auto& alien : aliens_) {
            maxY = std::max(maxY, alien.y);
        }
        return maxY;
    }

    void reset() {
        aliens_.clear();
        direction_ = 1;
        for (int row = 0; row < rows_; ++row) {
            for (int column = 0; column < columns_; ++column) {
                aliens_.push_back(Alien{
                    startX_ + column * 3,
                    startY_ + row * 2
                });
            }
        }
    }

private:
    struct Alien {
        int x;
        int y;
    };

    [[nodiscard]] std::pair<int, int> horizontalBounds() const {
        int minX = aliens_.front().x;
        int maxX = aliens_.front().x;
        for (const auto& alien : aliens_) {
            minX = std::min(minX, alien.x);
            maxX = std::max(maxX, alien.x);
        }
        return {minX, maxX};
    }

    int rows_;
    int columns_;
    int startX_;
    int startY_;
    int fieldWidth_;
    int direction_ = 1;
    std::vector<Alien> aliens_;
};

class Terminal {
public:
    Terminal() {
        std::cout << "\x1b[2J";
    }

    ~Terminal() {
        std::cout << "\x1b[0m\n";
    }

    void present(const Canvas& canvas) {
        std::cout << "\x1b[H" << canvas.str() << std::flush;
    }
};

class GameLoop {
public:
    GameLoop(Fleet& fleet, Canvas& canvas, Terminal& terminal)
        : fleet_(fleet), canvas_(canvas), terminal_(terminal) {}

    void run() {
        using Clock = std::chrono::steady_clock;
        constexpr double kUpdateInterval = 0.12;
        constexpr auto kFrameInterval = std::chrono::milliseconds(16);
        constexpr double kMaxFrameTime = 0.25;

        auto previous = Clock::now();
        double accumulator = 0.0;

        for (;;) {
            const auto frameStart = Clock::now();
            double frameTime =
                std::chrono::duration<double>(frameStart - previous).count();
            previous = frameStart;

            if (frameTime > kMaxFrameTime) {
                frameTime = kMaxFrameTime;
            }
            accumulator += frameTime;

            while (accumulator >= kUpdateInterval) {
                update();
                accumulator -= kUpdateInterval;
            }

            render();

            const auto frameEnd = Clock::now();
            const auto frameDuration = frameEnd - frameStart;
            if (frameDuration < kFrameInterval) {
                std::this_thread::sleep_for(kFrameInterval - frameDuration);
            }
        }
    }

private:
    void update() {
        fleet_.update();
        if (fleet_.bottom() >= canvas_.height() - 2) {
            fleet_.reset();
        }
    }

    void render() {
        canvas_.clear();
        canvas_.drawBorder();
        fleet_.draw(canvas_);
        terminal_.present(canvas_);
    }

    Fleet& fleet_;
    Canvas& canvas_;
    Terminal& terminal_;
};

int main() {
    constexpr int kWidth = 40;
    constexpr int kHeight = 20;

    Canvas canvas(kWidth, kHeight);
    Fleet fleet(3, 6, 4, 3, kWidth);
    Terminal terminal;
    GameLoop loop(fleet, canvas, terminal);

    loop.run();
}
```

## Build and run

On macOS, the system compiler is available after installing the Xcode Command Line Tools:

```sh
xcode-select --install
```

Compile and run from Terminal:

```sh
clang++ -std=c++20 -Wall -Wextra -Wpedantic alien_fleet.cpp -o alien_fleet
./alien_fleet
```

The first frame resembles:

```text
########################################
#                                      #
#                                      #
#   A  A  A  A  A  A                   #
#                                      #
#   A  A  A  A  A  A                   #
#                                      #
#   A  A  A  A  A  A                   #
#                                      #
#                                      #
#                                      #
#                                      #
#                                      #
#                                      #
#                                      #
#                                      #
#                                      #
#                                      #
#                                      #
########################################
```

`Ctrl+C` stops the program. The cursor is not hidden and the terminal is not put into raw mode, so the shell remains usable.

## How the motion works

`Fleet::update` first finds the leftmost and rightmost occupied columns:

```cpp
const auto [minX, maxX] = horizontalBounds();
```

The interior of the canvas spans columns 1 through `fieldWidth - 2`; columns 0 and `fieldWidth - 1` are the border. The fleet is at the right edge when:

```cpp
direction_ > 0 && maxX >= fieldWidth_ - 2
```

It is at the left edge when:

```cpp
direction_ < 0 && minX <= 1
```

At either edge, the direction reverses and every alien's row increases by one:

```cpp
direction_ = -direction_;
for (auto& alien : aliens_) {
    ++alien.y;
}
```

Otherwise, every alien moves one column in the current direction:

```cpp
for (auto& alien : aliens_) {
    alien.x += direction_;
}
```

There is no horizontal move on a bounce. The reversal and the drop occur in the same update. That is the familiar Space Invaders fleet behaviour.

When `bottom()` reaches the last usable row, `GameLoop::update` calls `reset()`. This is a demo convenience, not game logic; a real game would end or change state.

## The game loop class

`GameLoop::run` follows the fixed-timestep pattern from `chrspaceinvaders/main.cpp`:

- Read the elapsed wall-clock time.
- Clamp excessively long frames to avoid an unbounded catch-up loop after a stall.
- Add the elapsed time to an accumulator.
- Run `update()` once for every fixed interval in the accumulator.
- Call `render()` once for the current display frame.
- Sleep for the remainder of the 16 ms frame interval.

`kUpdateInterval` is 0.12 seconds, so the fleet advances about eight times per second. `kFrameInterval` is 16 milliseconds, which gives the renderer an upper bound of roughly 60 frames per second. The terminal output is small enough that the sleep dominates.

The source game-loop file uses an interpolation factor, alpha, because its simulation state contains continuous positions. This tutorial does not use alpha: the aliens occupy discrete character cells, and a position between two cells has no meaningful character representation. Adding interpolation here would require floating-point alien positions and a separate render position; that is unnecessary for a character-grid fleet.

## Why the classes are split this way

`Canvas` is a pure output buffer. It uses `std::vector<char>` and bounds-checked `set` calls, so the motion code cannot write outside the canvas.

`clear()` uses `std::ranges::fill(cells_, ' ')` rather than `std::fill(cells_.begin(), cells_.end(), ' ')`. The ranges form takes the container directly, so the begin and end iterators cannot be mismatched. This requires C++20, which the build command already selects.

`Fleet` is a pure state machine over positions. It uses `std::vector<Alien>` and stores only the data it needs: x, y, and a direction. `update`, `draw`, and `bottom` are `const` where they do not modify state.

`Terminal` isolates the escape sequences:

- `\x1b[2J` clears the screen.
- `\x1b[H` moves the cursor to the top-left.
- `\x1b[0m` resets terminal attributes.

The terminal is not cleared on every frame. The cursor is moved home and the full canvas overwrites the previous frame. That avoids flicker and the cost of spawning `clear` or `cls` processes.

`GameLoop` owns time and the bottom-of-field reset. It uses `std::chrono::steady_clock`, a fixed update interval, and a simple frame limiter. The loop is infinite; `Ctrl+C` terminates it.

## macOS portability notes

- Do not include `conio.h`, `windows.h`, or call `system("cls")`.
- ANSI sequences are supported by Terminal.app and iTerm2. If an IDE run window shows raw escape codes, run the program in the integrated terminal or Terminal.app.
- The program does not require raw terminal mode because it only writes output. If keyboard input is added later, `termios` can put the terminal into non-canonical mode, and the original settings must be restored on every exit path.
- The program uses ASCII glyphs, so locale and Unicode width are not issues.

## What to change

- Change the fleet speed by changing `kUpdateInterval` in `GameLoop::run`.
- Change the render cap by changing `kFrameInterval`.
- Change the fleet size in `Fleet fleet(3, 6, 4, 3, kWidth)`.
- Change the field size with `kWidth` and `kHeight`.
- Change the alien glyph in `Fleet::draw` from `'A'` to another character.
- Change the spacing in `Fleet::reset` from `column * 3` and `row * 2`.

## What is deliberately missing

This is not a complete Space Invaders game. It has no player, input handling, shooting, collision detection, score, or game-over state. Those features belong in a later stage. The purpose here is to make the fleet movement, the fixed-timestep loop, and the rendering path observable in a program that compiles and runs on macOS.

## References

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/cgxm9z20u1lmqynire).
- Source game loop: [`chrspaceinvaders/main.cpp`](https://github.com/dlcmh/cppgamearch/blob/main/src/apps/chrspaceinvaders/main.cpp).
