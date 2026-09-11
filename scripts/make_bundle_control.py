"""Generate source-frozen ablations of the Step 7 opening and input valuation."""

import argparse
from pathlib import Path


def build(source, output, opening=True, fertilizer=True, crop_limit=12):
    code = Path(source).read_text()
    if code.count("\ndef agent(") != 1 or "\ndef bundle_turn(" not in code:
        raise ValueError("Expected the standalone bundle policy")
    if crop_limit not in (8, 12):
        raise ValueError("Use a validated crop-area bound")
    code = code.rsplit("\ndef agent(", 1)[0]
    code += (
        "\ndef agent(obs, configuration=None):\n"
        f"    return bundle_turn(obs, configuration, crop_limit={crop_limit}, "
        f"use_fertilizer={fertilizer!r}, opening={opening!r})[0]\n"
    )
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as f:
        f.write(code)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("main.py"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--no-opening", action="store_true")
    parser.add_argument("--no-fertilizer", action="store_true")
    parser.add_argument("--crop-limit", type=int, choices=[8, 12], default=12)
    a = parser.parse_args()
    build(a.source, a.output, not a.no_opening, not a.no_fertilizer, a.crop_limit)


if __name__ == "__main__":
    main()
