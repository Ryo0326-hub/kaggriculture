"""Build a standalone challenger with location-aware land candidate admission."""

import argparse
from pathlib import Path


def build(source, output):
    code = Path(source).read_text()
    old_gate = "if extra and (owned >= max_land or len(empty(fields)) > 6):"
    old_batch = "if count > len(possible) or extra and count <= len(empty(fields)):\n"
    new_batch = (
        "if count > len(possible) or (\n"
        "                extra\n"
        '                and not any(farm["tiles"][y][x] == "LOCKED" '
        "for x, y in possible[:count])\n"
        "            ):\n"
    )
    changes = {old_gate: "if extra and owned >= max_land:", old_batch: new_batch}
    for before, after in changes.items():
        if code.count(before) != 1:
            raise ValueError("Expected exactly one frozen land-admission rule")
        code = code.replace(before, after)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as file:
        file.write(code)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("baselines/cycle_3.py"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.source, args.output)


if __name__ == "__main__":
    main()
