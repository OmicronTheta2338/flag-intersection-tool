"""
intersect.py - Core flag intersection logic.

Performs a pixel-wise logical AND on two flag images:
  - Flags are NOT resized. They are aligned at the top-left corner.
  - Where Flag_A(x,y) is similar to Flag_B(x,y) within a tolerance -> keep Flag A's colour.
  - Where they differ beyond tolerance, or one flag doesn't reach (x,y) -> transparent / white.

Colour similarity is measured by Euclidean distance in RGB space.
"""

from pathlib import Path
from PIL import Image


WHITE = (255, 255, 255, 255)
TRANSPARENT = (0, 0, 0, 0)

DEFAULT_TOLERANCE = 10  # Euclidean RGB distance threshold (0 = exact match only)
# For reference: max possible Euclidean RGB distance = sqrt(3 * 255^2) ~= 441


def load_flag(path: str | Path) -> Image.Image:
    """Load a flag image at its native resolution and convert to RGBA."""
    return Image.open(path).convert("RGBA")


def _rgb_distance_sq(pa: tuple, pb: tuple) -> int:
    """Squared Euclidean distance between the RGB components of two RGBA pixels.
    Using squared distance avoids a sqrt and is sufficient for threshold comparisons."""
    return (pa[0] - pb[0]) ** 2 + (pa[1] - pb[1]) ** 2 + (pa[2] - pb[2]) ** 2


def intersect_flags(
    img_a: Image.Image,
    img_b: Image.Image,
    white_bg: bool = False,
    tolerance: int = DEFAULT_TOLERANCE,
) -> Image.Image:
    """
    Compare two RGBA images pixel-by-pixel, aligned at the top-left.

    The output canvas is max(width_a, width_b) x max(height_a, height_b).
    Pixels outside either flag's native bounds are treated as null and never
    match, so they always become transparent (or white).

    Colour matching uses Euclidean RGB distance:
      - distance <= tolerance  ->  pixels are "similar enough"; Flag A's colour is kept.
      - distance >  tolerance  ->  non-matching; result pixel = transparent / white.

    Tolerance guide:
      0   = exact pixel equality only (strict mode)
      10  = default; invisible to the human eye, catches compression/rendering artefacts
      30  = catches noticeably similar shades (e.g. slightly different reds)
      50+ = broad tolerance; large colour regions will match
    """
    w = max(img_a.width, img_b.width)
    h = max(img_a.height, img_b.height)

    fill = WHITE if white_bg else TRANSPARENT
    threshold_sq = tolerance * tolerance  # compare squared distances to avoid sqrt

    # Paste each flag onto a blank (transparent) canvas of the union size.
    # Regions not covered by a flag stay TRANSPARENT (0,0,0,0) = "out of bounds".
    canvas_a = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas_b = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    canvas_a.paste(img_a, (0, 0))
    canvas_b.paste(img_b, (0, 0))

    pixels_a = list(canvas_a.getdata())
    pixels_b = list(canvas_b.getdata())

    result_pixels = []
    for pa, pb in zip(pixels_a, pixels_b):
        # A transparent canvas pixel means this (x,y) is outside that flag's bounds.
        # Out-of-bounds pixels are treated as null and never match.
        if pa[3] == 0 or pb[3] == 0:
            result_pixels.append(fill)
        elif _rgb_distance_sq(pa, pb) <= threshold_sq:
            result_pixels.append(pa)  # similar enough -> keep Flag A's colour
        else:
            result_pixels.append(fill)

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

    # Formats that don't support alpha - flatten onto white
    if fmt_upper in ("BMP", "JPEG", "JPG"):
        background = Image.new("RGBA", img.size, WHITE)
        background.paste(img, mask=img.split()[3])  # use alpha channel as mask
        img = background.convert("RGB")
        img.save(str(output_path), format=fmt_upper if fmt_upper != "JPG" else "JPEG")
    else:
        img.save(str(output_path), format=fmt_upper)

    return output_path
