"""Freeze a crop-menu, crop-area, or fertilizer ablation of the mixed policy."""

import argparse
from pathlib import Path


def build(source, output, crop_limit=8, fertilizer=True, crops=("WHEAT", "MELON", "STRAWBERRY")):
    if (
        not 0 <= crop_limit <= 12
        or not crops
        or any(c not in ("WHEAT", "MELON", "STRAWBERRY") for c in crops)
    ):
        raise ValueError("Unsupported crop menu or area bound")
    code = Path(source).read_text()
    if code.count("\ndef agent(") != 1 or "\ndef mixed_turn(" not in code:
        raise ValueError("Expected a mixed policy with one final entry point")
    code = code.rsplit("\ndef agent(", 1)[0]
    code += (
        "\ndef agent(obs, configuration=None):\n"
        f"    return mixed_turn(obs, configuration, crop_limit={crop_limit!r}, "
        f"use_fertilizer={fertilizer!r}, allowed_crops={tuple(crops)!r})[0]\n"
    )
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as f:
        f.write(code)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("main.py"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--crop-limit", type=int, default=8)
    parser.add_argument("--no-fertilizer", action="store_true")
    parser.add_argument(
        "--crops",
        nargs="+",
        choices=["WHEAT", "MELON", "STRAWBERRY"],
        default=["WHEAT", "MELON", "STRAWBERRY"],
    )
    a = parser.parse_args()
    build(a.source, a.output, a.crop_limit, not a.no_fertilizer, a.crops)


if __name__ == "__main__":
    main()
