from __future__ import annotations

import binascii
import struct
import zlib
from pathlib import Path


NAVY = (20, 40, 61, 255)
TEAL = (15, 118, 110, 255)
BLUE = (62, 113, 153, 255)
AMBER = (217, 119, 6, 255)
WHITE = (255, 255, 255, 255)


def png_chunk(kind: bytes, payload: bytes) -> bytes:
    return (
        struct.pack(">I", len(payload))
        + kind
        + payload
        + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)
    )


def make_png(size: int) -> bytes:
    scale = 4
    width = height = size * scale
    pixels = bytearray(width * height * 4)

    def set_pixel(x: int, y: int, color: tuple[int, int, int, int]) -> None:
        if 0 <= x < width and 0 <= y < height:
            offset = (y * width + x) * 4
            pixels[offset : offset + 4] = bytes(color)

    radius = int(width * 0.19)
    for y in range(height):
        for x in range(width):
            inside = True
            if x < radius and y < radius:
                inside = (x - radius) ** 2 + (y - radius) ** 2 <= radius**2
            elif x >= width - radius and y < radius:
                inside = (x - (width - radius - 1)) ** 2 + (y - radius) ** 2 <= radius**2
            elif x < radius and y >= height - radius:
                inside = (x - radius) ** 2 + (y - (height - radius - 1)) ** 2 <= radius**2
            elif x >= width - radius and y >= height - radius:
                inside = (
                    (x - (width - radius - 1)) ** 2
                    + (y - (height - radius - 1)) ** 2
                    <= radius**2
                )
            set_pixel(x, y, NAVY if inside else (0, 0, 0, 0))

    bars = [
        (0.19, 0.66, 0.11, TEAL),
        (0.36, 0.49, 0.11, BLUE),
        (0.53, 0.36, 0.11, TEAL),
        (0.70, 0.22, 0.11, AMBER),
    ]
    for x_ratio, y_ratio, bar_width, color in bars:
        x0 = int(width * x_ratio)
        x1 = int(width * (x_ratio + bar_width))
        y0 = int(height * y_ratio)
        y1 = int(height * 0.79)
        corner = max(2, int(width * 0.025))
        for y in range(y0, y1):
            for x in range(x0, x1):
                if y < y0 + corner:
                    cx = x0 + corner if x < x0 + corner else x1 - corner - 1
                    if x < x0 + corner or x >= x1 - corner:
                        if (x - cx) ** 2 + (y - (y0 + corner)) ** 2 > corner**2:
                            continue
                set_pixel(x, y, color)

    points = [
        (int(width * 0.24), int(height * 0.56)),
        (int(width * 0.42), int(height * 0.41)),
        (int(width * 0.59), int(height * 0.29)),
        (int(width * 0.76), int(height * 0.15)),
    ]
    thickness = max(2, int(width * 0.025))
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        steps = max(abs(x1 - x0), abs(y1 - y0))
        for step in range(steps + 1):
            x = round(x0 + (x1 - x0) * step / steps)
            y = round(y0 + (y1 - y0) * step / steps)
            for dy in range(-thickness, thickness + 1):
                for dx in range(-thickness, thickness + 1):
                    if dx * dx + dy * dy <= thickness * thickness:
                        set_pixel(x + dx, y + dy, WHITE)

    reduced = bytearray(size * size * 4)
    for y in range(size):
        for x in range(size):
            sums = [0, 0, 0, 0]
            for sy in range(scale):
                for sx in range(scale):
                    source = (((y * scale + sy) * width) + x * scale + sx) * 4
                    for channel in range(4):
                        sums[channel] += pixels[source + channel]
            target = (y * size + x) * 4
            reduced[target : target + 4] = bytes(value // (scale * scale) for value in sums)

    scanlines = bytearray()
    stride = size * 4
    for y in range(size):
        scanlines.append(0)
        scanlines.extend(reduced[y * stride : (y + 1) * stride])
    signature = b"\x89PNG\r\n\x1a\n"
    header = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    return (
        signature
        + png_chunk(b"IHDR", header)
        + png_chunk(b"IDAT", zlib.compress(bytes(scanlines), 9))
        + png_chunk(b"IEND", b"")
    )


def build_ico(destination: Path) -> None:
    sizes = [16, 24, 32, 48, 64, 128, 256]
    images = [(size, make_png(size)) for size in sizes]
    directory_size = 6 + 16 * len(images)
    entries = bytearray()
    payload = bytearray()
    offset = directory_size
    for size, image in images:
        entries.extend(
            struct.pack(
                "<BBBBHHII",
                0 if size == 256 else size,
                0 if size == 256 else size,
                0,
                0,
                1,
                32,
                len(image),
                offset,
            )
        )
        payload.extend(image)
        offset += len(image)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(
        struct.pack("<HHH", 0, 1, len(images)) + bytes(entries) + bytes(payload)
    )


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    output = project_root / "assets" / "app_icon.ico"
    build_ico(output)
    print(f"Created {output}")
