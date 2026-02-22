"""
cli.py — Command-line interface for the Flag Intersection Tool.

Usage:
    python cli.py <flag_a> <flag_b> [--output PATH] [--size WxH] [--white-bg]

Examples:
    python cli.py flags/france.png flags/netherlands.png
    python cli.py flags/a.bmp flags/b.bmp --output output/result.bmp
    python cli.py flags/a.png flags/b.png --size 800x600 --white-bg
"""

import argparse
import sys
from pathlib import Path

from intersect import load_flag, intersect_flags, save_result


def derive_output_path(flag_a: Path, flag_b: Path) -> Path:
    """Build a default output path from the two input flag names."""
    stem_a = flag_a.stem
    stem_b = flag_b.stem
    ext = flag_a.suffix  # match format of first input
    return Path("output") / f"{stem_a}_AND_{stem_b}{ext}"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="flag-intersect",
        description=(
            "Perform a pixel-wise logical AND on two flag images.\n"
            "Matching pixels are kept; differing pixels become transparent (or white)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("flag_a", type=Path, help="Path to the first flag image.")
    parser.add_argument("flag_b", type=Path, help="Path to the second flag image.")
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output file path. Defaults to output/<a>_AND_<b>.<ext>.",
    )
    parser.add_argument(
        "--white-bg",
        action="store_true",
        help="Use white background for non-matching pixels instead of transparency.",
    )

    args = parser.parse_args()

    # Validate inputs
    for path, label in [(args.flag_a, "flag_a"), (args.flag_b, "flag_b")]:
        if not path.exists():
            print(f"Error: {label} file not found: {path}", file=sys.stderr)
            sys.exit(1)
        if not path.is_file():
            print(f"Error: {label} is not a file: {path}", file=sys.stderr)
            sys.exit(1)

    # Determine output path & format
    output_path = args.output or derive_output_path(args.flag_a, args.flag_b)
    # Format is determined by the OUTPUT extension (or flag_a's extension if default)
    fmt = output_path.suffix.lstrip(".").upper() or args.flag_a.suffix.lstrip(".").upper()
    if not fmt:
        fmt = "PNG"

    print("Loading flags at native resolution...")
    img_a = load_flag(args.flag_a)
    img_b = load_flag(args.flag_b)

    print("Computing intersection...")
    result = intersect_flags(img_a, img_b, white_bg=args.white_bg)

    print(f"Saving result to: {output_path}")
    save_result(result, output_path, fmt)

    # Quick stats
    total_pixels = result.size[0] * result.size[1]
    kept = sum(1 for p in result.getdata() if p[3] > 0)
    pct = 100 * kept / total_pixels
    print(f"Done. {kept:,} / {total_pixels:,} pixels matched ({pct:.1f}%).")


if __name__ == "__main__":
    main()
