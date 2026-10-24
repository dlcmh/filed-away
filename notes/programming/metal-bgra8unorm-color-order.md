# Why BGRA8Unorm does not mean BGR colors in a Metal shader

> Based on a DeepSeek conversation about `MTL::PixelFormatBGRA8Unorm` in metal-cpp: [shared conversation](https://chat.deepseek.com/share/21fyxrgnnomvcea8nz).

Setting a drawable or texture to `MTL::PixelFormatBGRA8Unorm` does not require the fragment shader to return colors in BGR order. The pixel format describes how color components are stored in memory. The shader continues to use the logical RGBA order.

On a `CA::MetalLayer`, the setting appears as:

```cpp
layer->setPixelFormat(MTL::PixelFormatBGRA8Unorm);
```

The format applies to the layer's drawable textures; it does not change the component order used by shader code.

## What the format name describes

`BGRA8Unorm` is a memory-layout description:

- **B, G, R, A** are the byte order in memory.
- **8** means eight bits per component.
- **Unorm** means an unsigned normalized integer: the stored integer is mapped to a floating-point range, typically 0 to 255 becoming 0.0 to 1.0.

A red pixel in a `BGRA8Unorm` texture therefore has memory bytes approximately `00 00 FF FF`: blue = 0, green = 0, red = 255, alpha = 255.

## What the shader sees

A Metal fragment shader works with logical components:

```metal
fragment float4 fragmentMain(VertexOutput in [[stage_in]]) {
    return float4(1.0, 0.0, 0.0, 1.0);  // logical RGBA: red
}
```

The `float4` is RGBA regardless of the render target's pixel format. The render pipeline uses the destination format to write those components into the correct byte positions. For a `BGRA8Unorm` target, the GPU reorders the red, green, blue, and alpha values into B, G, R, A order in memory.

The same rule applies to clear values. A clear color is specified in logical RGBA order:

```cpp
colorAttachment->setClearColor(MTL::ClearColorMake(1.0f, 0.0f, 0.0f, 1.0f));
```

No component swap is required in the shader or in the clear-color call.

## Why the name is reversed

The format name follows the physical storage sequence, not the logical color order used by shader code and image APIs. “RGB” describes the logical channels; “BGRA” describes the byte sequence a texture or drawable uses in memory.

Apple's graphics and windowing frameworks have historically used BGRA as a native layout. A `CAMetalLayer` and an `MTKView` commonly default to `BGRA8Unorm`. When the display path already expects BGRA, using the same format avoids an additional per-pixel reorder when the image is passed to system frameworks. Choosing RGBA can require a conversion step, depending on how the texture is consumed.

The naming convention is therefore not an instruction to write colors differently. It is a statement about what the memory contains.

## Where the byte order does matter

The distinction becomes important when the application reads or writes raw pixel bytes on the CPU.

If a texture is configured as `BGRA8Unorm` and the application uploads raw bytes, those bytes must already be in B, G, R, A order:

```cpp
// BGRA8Unorm: blue, green, red, alpha
std::uint8_t redPixel[] = { 0, 0, 255, 255 };
```

If the source image is stored as RGBA, the upload path must either convert the bytes to BGRA or use an RGBA texture format and accept the display-path consequences. The shader does not perform this conversion for CPU-provided buffers.

The same applies to readback. A byte buffer read from a `BGRA8Unorm` texture has blue in the first byte, not red:

```cpp
// pixels[0] is blue, pixels[1] is green,
// pixels[2] is red,  pixels[3] is alpha
```

## Choosing a format

- For a `CAMetalLayer` or `MTKView` that presents directly to the display, `BGRA8Unorm` is the conventional default on Apple platforms.
- For a texture whose CPU-side data is already RGBA, either convert the data during upload or use `RGBA8Unorm`.
- Do not change the shader's component order to match the pixel format. Keep shader colors in RGBA and let the pipeline map them to the destination layout.
- When reading or writing raw bytes, treat the pixel format as the contract for the byte sequence.

## Summary

`BGRA8Unorm` describes the byte order of the stored pixel, not the order of components in the shader. Fragment shaders and clear colors remain RGBA. The GPU performs the mapping to BGRA memory. Byte order becomes the application's responsibility only when it uploads or reads raw pixel data.

## References

- Apple, [`MTLPixelFormat.bgra8Unorm`](https://developer.apple.com/documentation/metal/mtlpixelformat/bgra8unorm).
- Apple, [`MTLPixelFormat`](https://developer.apple.com/documentation/metal/mtlpixelformat).
- Apple, [`CIFormat.bgra8`](https://developer.apple.com/documentation/coreimage/ciformat/bgra8).
- DeepSeek, [shared conversation](https://chat.deepseek.com/share/21fyxrgnnomvcea8nz).
