"""Create a matched control with fixed staffing, wheat-only production, or both."""

import argparse
from pathlib import Path


def build(source, output, fixed_hands=False, wheat_only=False, optimistic_prices=False):
    code = Path(source).read_text()
    if code.count("\ndef agent(") != 1:
        raise ValueError("Expected one final agent entry point")
    code = code.rsplit("\ndef agent(", 1)[0]
    code += (
        "\ndef agent(obs, configuration=None):\n"
        f"    return plan_turn(obs, configuration, fixed_hands={fixed_hands!r}, "
        f"wheat_only={wheat_only!r}, supply_buffer={not optimistic_prices!r})[0]\n"
    )
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as artifact:
        artifact.write(code)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("baselines/step_3.py"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--fixed-hands", action="store_true")
    parser.add_argument("--wheat-only", action="store_true")
    parser.add_argument("--optimistic-prices", action="store_true")
    args = parser.parse_args()
    if not args.fixed_hands and not args.wheat_only and not args.optimistic_prices:
        parser.error("Choose at least one economic ablation")
    build(args.source, args.output, args.fixed_hands, args.wheat_only, args.optimistic_prices)


if __name__ == "__main__":
    main()
