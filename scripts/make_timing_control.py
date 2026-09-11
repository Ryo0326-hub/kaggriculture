"""Freeze an isolated fertilizer/harvest timing challenger for the official loader."""

import argparse
from pathlib import Path

MODES = {"legacy": 0, "fertilizer": 1, "harvest": 2, "combined": 3}


def build(source, output, mode, bake_default=False):
    code = Path(source).read_text()
    if code.count("\ndef agent(") != 1 or "\ndef timing_fertilizer_value(" not in code:
        raise ValueError("Expected the standalone timing experiment")
    if bake_default:
        signature = "max_land=3, timing=0, investments=True"
        if code.count(signature) != 1:
            raise ValueError("Expected one expansion_turn default to configure")
        code = code.replace(signature, f"max_land=3, timing={MODES[mode]}, investments=True")
    code = code.rsplit("\ndef agent(", 1)[0]
    code += (
        "\ndef agent(obs, configuration=None):\n"
        f"    return expansion_turn(obs, configuration, timing={MODES[mode]})[0]\n"
    )
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as file:
        file.write(code)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("experiments/timing.py"))
    parser.add_argument("--mode", required=True, choices=MODES)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--bake-default", action="store_true")
    args = parser.parse_args()
    build(args.source, args.output, args.mode, args.bake_default)


if __name__ == "__main__":
    main()
