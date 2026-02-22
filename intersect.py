"""
intersect.py — Core flag intersection logic.

Performs a pixel-wise logical AND on two flag images:
  - Flags are NOT resized. They are aligned at the top-left corner.
  - Where Flag_A(x,y) == Flag_B(x,y)  →  Result(x,y) = that colour.
  - Where they differ, or one flag doesn't reach (x,y)  →  transparent / white.
"""

from pathlib import Path
from PIL import Image


WHITE = (255, 255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)


def load_flag(path: str | Path) -> Image.Image:
    """Load a flag image at its native resolution and convert to RGBA."""
    return Image.open(path).convert("RGBA")


def intersect_flags(
    img_a: Image.Image,
    img_b: Image.Image,
    white_bg: bool = False,
) -> Image.Image:
    """
    Compare two RGBA images pixel-by-pixel, aligned at the top-left.

    The output canvas is max(width_a, width_b) × max(height_a, height_b).
    Pixels outside either flag's native bounds are treated as null and never
    match, so they always become transparent (or white).

    Where pixels match → keep the pixel.
    Where pixels differ or one flag has no pixel there → transparent / white.
    """
    w = max(img_a.width, img_b.width)
    h = max(img_a.height, img_b.height)

    fill = WHITE if white_bg else TRANSPARENT

    # Paste each flag onto a blank (transparent) canvas of the union size.
    # Any region not covered by a flag stays as TRANSPARENT (0,0,0,0).
    canvas_a = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas_b = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas_a.paste(img_a, (0, 0))
    canvas_b.paste(img_b, (0, 0))

    pixels_a = list(canvas_a.getdata())
    pixels_b = list(canvas_b.getdata())

    result_pixels = [
        pa if pa == pb else fill
        for pa, pb in zip(pixels_a, pixels_b)
    ]

    result = Image.new("RGBA", (w, h))
    result.putdata(result_pixels)
    return result


def save_result(img: Image.Image, output_path: str | Path, fmt: str) -> Path:
    """
    Save the result image in the desired format.

    For formats that don't support transparency (BMP, JPEG),
    the image is composited onto a white background first.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fmt_upper = fmt.upper()

    # Formats that don't support alpha — flatten onto white
    if fmt_upper in ("BMP", "JPEG", "JPG"):
        background = Image.new("RGBA", img.size, WHITE)
        background.paste(img, mask=img.split()[3])  # use alpha channel as mask
        img = background.convert("RGB")
        output_path.write_bytes(b"")  # ensure file is writable
        img.save(str(output_path), format=fmt_upper if fmt_upper != "JPG" else "JPEG")
    else:
        img.save(str(output_path), format=fmt_upper)

    return output_path
