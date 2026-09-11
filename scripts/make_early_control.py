"""Freeze the independent early crop seller with an optional inventory delay."""

import argparse
from pathlib import Path


def build(source, output, delay=0):
    if not 0 <= delay <= 29:
        raise ValueError("Sale delay must be a day in the season")
    code = Path(source).read_text()
    if code.count("DELAY_SALES_UNTIL = 0") != 1:
        raise ValueError("Expected the independent early crop control")
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as f:
        f.write(code.replace("DELAY_SALES_UNTIL = 0", f"DELAY_SALES_UNTIL = {delay}"))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=Path("opponents/early_crops.py"))
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--delay-sales-until", type=int, default=0)
    a = p.parse_args()
    build(a.source, a.output, a.delay_sales_until)


if __name__ == "__main__":
    main()
