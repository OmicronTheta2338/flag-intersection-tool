"""
cli.py - Command-line interface for the Flag Intersection Tool.

Usage:
    python cli.py <flag1> <flag2> [<flag3> ...] [--output PATH] [--tolerance N] [--white-bg]

Examples:
    python cli.py flags/fr.png flags/nl.png
    python cli.py flags/fr.png flags/de.png flags/be.png
    python cli.py flags/fr.png flags/nl.png --tolerance 30 --output output/result.png
    python cli.py flags/fr.bmp flags/de.bmp --white-bg
"""

import argparse
import sys
from pathlib import Path

from intersect import load_flag, intersect_many, save_result, DEFAULT_TOLERANCE


def derive_output_path(flag_paths: list[Path]) -> Path:
    """Build a default output path by joining all flag stems with _AND_."""
    stems = "_AND_".join(p.stem for p in flag_paths)
    ext = flag_paths[0].suffix  # match format of first input
    return Path("output") / f"{stems}{ext}"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="flag-intersect",
        description=(
            "Perform a pixel-wise logical AND on two or more flag images.\n"
            "Matching pixels are kept; differing pixels become transparent (or white)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "flags",
        type=Path,
        nargs="+",
        metavar="FLAG",
        help="Two or more flag image paths to intersect.",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output file path. Defaults to output/<a>_AND_<b>_AND_...<ext>.",
    )
    parser.add_argument(
        "--tolerance", "-t",
        type=int,
        default=DEFAULT_TOLERANCE,
        metavar="N",
        help=(
            f"Max Euclidean RGB distance for two pixels to be considered matching "
            f"(0=exact, default={DEFAULT_TOLERANCE}). "
            f"~10 fixes compression artefacts, ~30 catches similar shades."
        ),
    )
    parser.add_argument(
        "--white-bg",
        action="store_true",
        help="Use white background for non-matching pixels instead of transparency.",
    )

    args = parser.parse_args()

    if len(args.flags) < 2:
        parser.error("At least 2 flag images are required.")

    # Validate all inputs
    for path in args.flags:
        if not path.exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        if not path.is_file():
            print(f"Error: not a file: {path}", file=sys.stderr)
            sys.exit(1)

    # Determine output path & format
    output_path = args.output or derive_output_path(args.flags)
    fmt = output_path.suffix.lstrip(".").upper() or args.flags[0].suffix.lstrip(".").upper()
    if not fmt:
        fmt = "PNG"

    n = len(args.flags)
    print(f"Loading {n} flags at native resolution...")
    images = [load_flag(p) for p in args.flags]
    for p, img in zip(args.flags, images):
        print(f"  {p.name}: {img.size[0]}x{img.size[1]}")

    print(f"Computing intersection of {n} flags (tolerance={args.tolerance})...")
    result = intersect_many(images, white_bg=args.white_bg, tolerance=args.tolerance)

    print(f"Saving result to: {output_path}")
    save_result(result, output_path, fmt)

    # Quick stats
    total_pixels = result.size[0] * result.size[1]
    kept = sum(1 for p in result.getdata() if p[3] > 0)
    pct = 100 * kept / total_pixels
    print(f"Done. {kept:,} / {total_pixels:,} pixels matched ({pct:.1f}%).")


if __name__ == "__main__":
    main()
