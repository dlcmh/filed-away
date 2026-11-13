# PTO-ISA: a portable tile ISA for Ascend, with a CPU simulator

> Based on a DeepSeek conversation about the `pto-isa` repository: [shared conversation](https://chat.deepseek.com/share/mcsfkway36lbwxrjab).

The `pto-isa` repository defines and implements **PTO** (Parallel Tile Operation), a virtual instruction set architecture for programming Huawei Ascend NPUs. It is not only a laptop development kit, but it does support laptop development through a CPU simulator.

## Why the repository exists

Ascend hardware spans multiple generations. Code written directly against one generation's low-level details is difficult to move to another. PTO provides a tile-level abstraction that sits above those details.

The repository contains:

- header files for kernel compilation;
- implementations of the tile instructions;
- examples and documentation;
- support for the Ascend `a2a3` platform.

It defines more than 90 standard tile instructions. The goal is a cross-generation programming layer that preserves portability while still allowing performance tuning. The repository is the open-source home of the PTO Tile Library, not merely a collection of examples.

The intended users are framework developers, compiler engineers, operator developers, and performance engineers who need to write or generate kernels for Ascend hardware.

## Developing without Ascend hardware

The repository includes a **CPU simulator** for functional verification and debugging. The CPU path requires Python, CMake, and a C++20-capable compiler. It is intended for quick cross-platform validation on macOS, Linux, or Windows.

This means a developer can:

- compile and exercise PTO kernels on a laptop;
- check functional correctness;
- debug tile-level logic;
- defer access to Ascend hardware until performance work is required.

The simulator does not make a laptop equivalent to an Ascend machine. It models the instruction behavior needed for functional testing, not the full timing and performance characteristics of the hardware.

## Simulator or emulator?

The repository uses the term **CPU Simulator**, not emulator. The distinction is useful:

- A **simulator** models behavior at a functional level. It is appropriate for checking whether a kernel produces the right result.
- An **emulator** typically attempts to reproduce hardware behavior instruction by instruction, often to run unmodified binaries. It is generally more complex and slower.

PTO's CPU backend is described as a simulator because its purpose is functional verification and development debugging. The repository names backends such as `a2a3sim` and `a5sim`, where `sim` stands for simulator. Development discussions refer to the CPU simulator backend and CPU-SIM validation.

For a beginner, the practical meaning is that the simulator can catch logic errors but cannot indicate how fast a kernel will run on real Ascend silicon.

## What it is not

The CPU simulator is not a performance model. It does not replace profiling on the target hardware, and it does not model every timing detail of the NPU. Performance-sensitive decisions still require real hardware or a cycle-accurate model.

The repository is also not a general-purpose C++ library. It is an ISA and kernel-development layer tied to the Ascend ecosystem.

## Summary

- `pto-isa` provides the PTO virtual ISA, headers, implementations, examples, and documentation for Ascend kernels.
- Its main purpose is portable tile-level programming across Ascend generations.
- It supports laptop development through a CPU simulator that needs Python, CMake, and a C++20 compiler.
- The tool is a functional simulator, not an emulator and not a performance model.
- It lets developers validate kernel logic before moving to Ascend hardware for timing and optimization.

## Reference

- DeepSeek, [shared conversation](https://chat.deepseek.com/share/mcsfkway36lbwxrjab).
