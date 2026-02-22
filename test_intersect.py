"""
test_intersect.py — Automated tests for intersect.py.

Uses real flags from the flags/ database.
Run with:
    python test_intersect.py
"""

from PIL import Image
from pathlib import Path
from intersect import intersect_flags, load_flag, save_result, TRANSPARENT, WHITE
import tempfile
import os


FLAGS_DIR = Path("flags")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_image(pixels: list[tuple], size=(4, 2)) -> Image.Image:
    """Create a small RGBA test image from a flat pixel list."""
    img = Image.new("RGBA", size)
    img.putdata(pixels)
    return img


RED  = (255,   0,   0, 255)
BLUE = (  0,   0, 255, 255)
FILL_W = (255, 255, 255, 255)


# ---------------------------------------------------------------------------
# Unit tests (synthetic images)
# ---------------------------------------------------------------------------

def test_identical_flags_return_same():
    """When both flags are identical, every pixel should be kept."""
    pixels = [RED, BLUE, FILL_W, RED, BLUE, FILL_W, RED, BLUE]
    img_a = make_image(pixels)
    img_b = make_image(pixels)
    result = intersect_flags(img_a, img_b)
    assert list(result.getdata()) == pixels, "Identical flags should produce identical result"
    print("PASS: test_identical_flags_return_same")


def test_completely_different_flags_are_transparent():
    """When every pixel differs, result should be all-transparent."""
    img_a = make_image([RED]  * 8)
    img_b = make_image([BLUE] * 8)
    result = intersect_flags(img_a, img_b)
    assert all(p == TRANSPARENT for p in result.getdata()), \
        "All-different flags should produce all-transparent result"
    print("PASS: test_completely_different_flags_are_transparent")


def test_partial_match():
    """Pixels that match are kept; others become transparent."""
    pixels_a = [RED, BLUE, RED, BLUE, RED, BLUE, RED, BLUE]
    pixels_b = [RED, RED,  RED, BLUE, RED, RED,  RED, BLUE]
    expected  = [RED, TRANSPARENT, RED, BLUE, RED, TRANSPARENT, RED, BLUE]
    result = intersect_flags(make_image(pixels_a), make_image(pixels_b))
    assert list(result.getdata()) == expected, f"Partial match failed: {list(result.getdata())}"
    print("PASS: test_partial_match")


def test_white_bg_option():
    """With white_bg=True, differing pixels should be white, not transparent."""
    pixels_a = [RED,  BLUE] * 4
    pixels_b = [BLUE, BLUE] * 4
    expected  = [WHITE, BLUE] * 4
    result = intersect_flags(make_image(pixels_a), make_image(pixels_b), white_bg=True)
    assert list(result.getdata()) == expected, f"White-bg test failed: {list(result.getdata())}"
    print("PASS: test_white_bg_option")


def test_different_sizes_canvas_is_union():
    """Output canvas should be max(w_a, w_b) × max(h_a, h_b)."""
    img_a = Image.new("RGBA", (6, 4), RED)
    img_b = Image.new("RGBA", (4, 6), RED)
    result = intersect_flags(img_a, img_b)
    assert result.size == (6, 6), f"Expected (6, 6), got {result.size}"
    print("PASS: test_different_sizes_canvas_is_union")


def test_out_of_bounds_pixels_are_transparent():
    """
    Pixels in the region covered by only one flag should always be transparent,
    because the other flag's canvas pixel is (0,0,0,0) there and won't match.
    """
    # img_a: 4×2 solid RED; img_b: 2×2 solid RED (narrower)
    # In the right half (x=2..3) img_b's canvas is TRANSPARENT — so even though
    # img_a is RED there, they don't match → result is TRANSPARENT.
    img_a = Image.new("RGBA", (4, 2), RED)
    img_b = Image.new("RGBA", (2, 2), RED)
    result = intersect_flags(img_a, img_b)
    assert result.size == (4, 2)
    pixels = list(result.getdata())
    # Left half (x=0,1 for both rows) → RED matches RED → kept
    left  = [pixels[0], pixels[1], pixels[4], pixels[5]]
    # Right half (x=2,3 for both rows) → out of img_b → transparent
    right = [pixels[2], pixels[3], pixels[6], pixels[7]]
    assert all(p == RED for p in left),  f"Left (overlap) pixels should be RED: {left}"
    assert all(p == TRANSPARENT for p in right), f"Right (outside img_b) pixels should be TRANSPARENT: {right}"
    print("PASS: test_out_of_bounds_pixels_are_transparent")


def test_save_and_reload_png():
    """Saved PNG result should reload with correct pixel data."""
    pixels = [RED, BLUE, TRANSPARENT, FILL_W] * 2
    img = make_image(pixels)
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "result.png")
        save_result(img, out_path, "PNG")
        reloaded = Image.open(out_path).convert("RGBA")
        assert list(reloaded.getdata()) == pixels, "PNG save/reload round-trip failed"
    print("PASS: test_save_and_reload_png")


def test_load_flag_is_native_size_and_rgba():
    """load_flag should return native resolution and RGBA mode (no resizing)."""
    flag_path = FLAGS_DIR / "fr.png"
    loaded = load_flag(flag_path)
    original = Image.open(flag_path)
    assert loaded.size == original.size, \
        f"Size changed: expected {original.size}, got {loaded.size}"
    assert loaded.mode == "RGBA", f"Expected RGBA mode, got {loaded.mode}"
    print(f"PASS: test_load_flag_is_native_size_and_rgba  [{original.size}]")


# ---------------------------------------------------------------------------
# Integration tests (real flags from database)
# ---------------------------------------------------------------------------

def test_fr_nl_intersection():
    """France ∩ Netherlands — both have white in their design, some overlap expected."""
    img_a = load_flag(FLAGS_DIR / "fr.png")
    img_b = load_flag(FLAGS_DIR / "nl.png")
    result = intersect_flags(img_a, img_b)
    # Canvas should be the union of their sizes
    expected_w = max(img_a.width, img_b.width)
    expected_h = max(img_a.height, img_b.height)
    assert result.size == (expected_w, expected_h), \
        f"Canvas size mismatch: expected ({expected_w},{expected_h}), got {result.size}"
    total = result.width * result.height
    kept  = sum(1 for p in result.getdata() if p[3] > 0)
    pct   = 100 * kept / total
    print(f"PASS: test_fr_nl_intersection  [{kept:,}/{total:,} pixels = {pct:.1f}% match]")


def test_identical_real_flags():
    """Intersecting a flag with itself should preserve every pixel."""
    img = load_flag(FLAGS_DIR / "de.png")
    result = intersect_flags(img, img)
    original_pixels = list(img.getdata())
    result_pixels   = list(result.getdata())
    assert original_pixels == result_pixels, \
        "Self-intersection of a flag should be the flag itself"
    print("PASS: test_identical_real_flags  [de.png AND de.png == de.png]")


def test_output_format_is_png():
    """CLI saves the result as PNG when inputs are PNG."""
    img_a = load_flag(FLAGS_DIR / "fr.png")
    img_b = load_flag(FLAGS_DIR / "de.png")
    result = intersect_flags(img_a, img_b)
    with tempfile.TemporaryDirectory() as tmpdir:
        out = os.path.join(tmpdir, "fr_AND_de.png")
        save_result(result, out, "PNG")
        reopened = Image.open(out)
        fmt = reopened.format
        reopened.close()
        assert fmt == "PNG", f"Expected PNG, got {fmt}"
    print("PASS: test_output_format_is_png")


if __name__ == "__main__":
    tests = [
        # Synthetic unit tests
        test_identical_flags_return_same,
        test_completely_different_flags_are_transparent,
        test_partial_match,
        test_white_bg_option,
        test_different_sizes_canvas_is_union,
        test_out_of_bounds_pixels_are_transparent,
        test_save_and_reload_png,
        # Real-flag tests
        test_load_flag_is_native_size_and_rgba,
        test_fr_nl_intersection,
        test_identical_real_flags,
        test_output_format_is_png,
    ]
    failures = 0
    for test in tests:
        try:
            test()
        except Exception as e:
            import traceback
            print(f"FAIL: {test.__name__} — {e}")
            traceback.print_exc()
            failures += 1

    print()
    if failures == 0:
        print(f"All {len(tests)} tests passed!")
    else:
        print(f"{failures} / {len(tests)} tests FAILED.")
        exit(1)
