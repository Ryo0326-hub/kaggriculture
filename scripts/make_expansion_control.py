"""Freeze a land-limit ablation while keeping the same Step 8 executable policy."""

import argparse
from pathlib import Path


def build(source, output, max_land):
    if max_land not in (1, 2, 3):
        raise ValueError("Use one, two, or three owned quadrants")
    code = Path(source).read_text()
    if code.count("\ndef agent(") != 1 or "\ndef expansion_turn(" not in code:
        raise ValueError("Expected the standalone expansion policy")
    code = code.rsplit("\ndef agent(", 1)[0]
    code += (
        "\ndef agent(obs, configuration=None):\n"
        f"    return expansion_turn(obs, configuration, max_land={max_land})[0]\n"
    )
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as file:
        file.write(code)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("main.py"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-land", type=int, choices=[1, 2, 3], required=True)
    args = parser.parse_args()
    build(args.source, args.output, args.max_land)


if __name__ == "__main__":
    main()
