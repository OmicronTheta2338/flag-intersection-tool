"""
test_intersect.py — Automated tests for intersect.py.

Run with:
    python test_intersect.py
"""

from PIL import Image
from intersect import intersect_flags, load_flag, save_result
import tempfile
import os


def make_image(pixels: list[tuple], size=(4, 2)) -> Image.Image:
    """Create a small RGBA test image from a flat pixel list."""
    img = Image.new("RGBA", size)
    img.putdata(pixels)
    return img


RED   = (255,   0,   0, 255)
BLUE  = (  0,   0, 255, 255)
WHITE = (255, 255, 255, 255)
TRANS = (  0,   0,   0,   0)


def test_identical_flags_return_same():
    """When both flags are identical, every pixel should be kept."""
    pixels = [RED, BLUE, WHITE, RED, BLUE, WHITE, RED, BLUE]
    img_a = make_image(pixels)
    img_b = make_image(pixels)
    result = intersect_flags(img_a, img_b)
    assert list(result.getdata()) == pixels, "Identical flags should produce identical result"
    print("PASS: test_identical_flags_return_same")


def test_completely_different_flags_are_transparent():
    """When every pixel differs, result should be all-transparent."""
    pixels_a = [RED]  * 8
    pixels_b = [BLUE] * 8
    img_a = make_image(pixels_a)
    img_b = make_image(pixels_b)
    result = intersect_flags(img_a, img_b)
    assert all(p == TRANS for p in result.getdata()), "All-different flags should produce all-transparent result"
    print("PASS: test_completely_different_flags_are_transparent")


def test_partial_match():
    """Pixels that match are kept; others become transparent."""
    pixels_a = [RED, BLUE, RED, BLUE, RED, BLUE, RED, BLUE]
    pixels_b = [RED, RED,  RED, BLUE, RED, RED,  RED, BLUE]
    #          [ =   ≠    =    =    =    ≠    =    =  ]
    expected  = [RED, TRANS, RED, BLUE, RED, TRANS, RED, BLUE]
    img_a = make_image(pixels_a)
    img_b = make_image(pixels_b)
    result = intersect_flags(img_a, img_b)
    assert list(result.getdata()) == expected, f"Partial match failed: {list(result.getdata())}"
    print("PASS: test_partial_match")


def test_white_bg_option():
    """With white_bg=True, differing pixels should be white, not transparent."""
    pixels_a = [RED,  BLUE]  * 4
    pixels_b = [BLUE, BLUE]  * 4
    #          [ ≠    =  ]
    expected  = [WHITE, BLUE] * 4
    img_a = make_image(pixels_a)
    img_b = make_image(pixels_b)
    result = intersect_flags(img_a, img_b, white_bg=True)
    assert list(result.getdata()) == expected, f"White-bg test failed: {list(result.getdata())}"
    print("PASS: test_white_bg_option")


def test_size_mismatch_raises():
    """Passing two images of different sizes should raise ValueError."""
    img_a = Image.new("RGBA", (4, 2))
    img_b = Image.new("RGBA", (8, 4))
    try:
        intersect_flags(img_a, img_b)
        assert False, "Should have raised ValueError"
    except ValueError:
        print("PASS: test_size_mismatch_raises")


def test_save_and_reload_png():
    """Saved PNG result should reload with correct pixel data."""
    pixels = [RED, BLUE, TRANS, WHITE] * 2
    img = make_image(pixels)
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = os.path.join(tmpdir, "result.png")
        save_result(img, out_path, "PNG")
        reloaded = Image.open(out_path).convert("RGBA")
        assert list(reloaded.getdata()) == pixels, "PNG save/reload round-trip failed"
    print("PASS: test_save_and_reload_png")


def test_load_flag_resizes():
    """load_flag should resize the image to the requested size."""
    # Create a tiny temp PNG
    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = os.path.join(tmpdir, "flag.png")
        tiny = Image.new("RGB", (10, 5), color=(200, 100, 50))
        tiny.save(src_path)
        loaded = load_flag(src_path, size=(300, 200))
        assert loaded.size == (300, 200), f"Expected (300, 200), got {loaded.size}"
        assert loaded.mode == "RGBA", f"Expected RGBA mode, got {loaded.mode}"
    print("PASS: test_load_flag_resizes")


if __name__ == "__main__":
    tests = [
        test_identical_flags_return_same,
        test_completely_different_flags_are_transparent,
        test_partial_match,
        test_white_bg_option,
        test_size_mismatch_raises,
        test_save_and_reload_png,
        test_load_flag_resizes,
    ]
    failures = 0
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"FAIL: {test.__name__} — {e}")
            failures += 1

    print()
    if failures == 0:
        print(f"All {len(tests)} tests passed!")
    else:
        print(f"{failures} / {len(tests)} tests FAILED.")
        exit(1)
