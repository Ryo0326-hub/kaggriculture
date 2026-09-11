"""Freeze one scheduling ablation as a standalone agent file."""

import argparse
from pathlib import Path

MODES = {
    "legacy": {},
    "open_routes": {"overnight": True, "dated_staffing": False},
    "dated_closed": {"overnight": False, "dated_staffing": True},
    "dated_open": {"overnight": True, "dated_staffing": True},
    "forecast_only": {"staffing_forecast": True},
    "open_forecast": {"overnight": True, "staffing_forecast": True},
    "combined": {"overnight": True, "dated_staffing": True, "staffing_forecast": True},
}


def build(source, output, mode):
    code = Path(source).read_text()
    if code.count("\ndef agent(") != 1 or "\ndef crop_route_staffing(" not in code:
        raise ValueError("Expected the standalone staffing policy")
    kwargs = ", ".join(f"{key}={value!r}" for key, value in MODES[mode].items())
    code = code.rsplit("\ndef agent(", 1)[0]
    code += (
        "\ndef agent(obs, configuration=None):\n"
        f"    return expansion_turn(obs, configuration{', ' if kwargs else ''}{kwargs})[0]\n"
    )
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as file:
        file.write(code)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=Path("experiments/staffing.py"), type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--mode", required=True, choices=MODES)
    args = parser.parse_args()
    build(args.source, args.output, args.mode)


if __name__ == "__main__":
    main()
