"""Create a frozen single-species or smaller-herd control from the current agent."""

import argparse
from pathlib import Path


def build(source, output, animal=None, herd_limit=10):
    code = Path(source).read_text()
    if code.count("\ndef agent(") != 1:
        raise ValueError("Expected one final agent entry point")
    if animal not in (None, "COW", "SHEEP", "GOOSE") or not 1 <= herd_limit <= 10:
        raise ValueError("Unsupported species or herd limit")
    allowed = (animal,) if animal else ("COW", "SHEEP")
    code = code.rsplit("\ndef agent(", 1)[0]
    code += (
        "\ndef agent(obs, configuration=None):\n"
        f"    return plan_turn(obs, configuration, allowed_animals={allowed!r}, "
        f"herd_limit={herd_limit!r})[0]\n"
    )
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as file:
        file.write(code)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("main.py"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--animal", choices=["COW", "SHEEP", "GOOSE"])
    parser.add_argument("--herd-limit", type=int, default=10)
    args = parser.parse_args()
    build(args.source, args.output, args.animal, args.herd_limit)


if __name__ == "__main__":
    main()
