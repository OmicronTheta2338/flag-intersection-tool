"""
intersect.py — Core flag intersection logic.

Performs a pixel-wise logical AND on two flag images:
  - If pixel at (x, y) is identical in both flags → keep it.
  - Otherwise → transparent (RGBA) or white (non-alpha formats).
"""

from pathlib import Path
from PIL import Image


DEFAULT_SIZE = (1200, 800)
WHITE = (255, 255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)


def load_flag(path: str | Path, size: tuple[int, int] = DEFAULT_SIZE) -> Image.Image:
    """Load a flag image, resize it, and convert to RGBA."""
    img = Image.open(path).convert("RGBA")
    img = img.resize(size, Image.LANCZOS)
    return img


def intersect_flags(
    img_a: Image.Image,
    img_b: Image.Image,
    white_bg: bool = False,
) -> Image.Image:
    """
    Compare two RGBA images pixel-by-pixel.

    Where pixels match → keep the pixel.
    Where pixels differ → transparent (or white if white_bg=True).

    Both images must be the same size. Use load_flag() to ensure this.
    """
    if img_a.size != img_b.size:
        raise ValueError(
            f"Images must be the same size. Got {img_a.size} and {img_b.size}."
        )

    pixels_a = list(img_a.getdata())
    pixels_b = list(img_b.getdata())

    fill = WHITE if white_bg else TRANSPARENT

    result_pixels = [
        pa if pa == pb else fill
        for pa, pb in zip(pixels_a, pixels_b)
    ]

    result = Image.new("RGBA", img_a.size)
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
