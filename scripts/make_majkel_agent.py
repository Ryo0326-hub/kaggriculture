"""Build Cycle 19 without importing any game engine or running a match."""

import argparse
import ast
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT_HASH = "47c281bfb4118a9755f1759930b162de007efdfef3b23144457eccbaac42da0c"
CORE = {
    "MARKET",
    "SHOP_PRODUCTS",
    "ANIMALS",
    "shape",
    "price_at",
    "batch_revenue",
    "distance",
    "move_toward",
    "hire_cost",
    "observed_demand",
}


def source():
    parent = (ROOT / "baselines/cycle_3.py").read_text()
    if sha256(parent.encode()).hexdigest() != PARENT_HASH:
        raise ValueError("Protected mechanics source changed")
    parts = []
    found = set()
    for node in ast.parse(parent).body:
        name = (
            node.name
            if isinstance(node, ast.FunctionDef)
            else (
                node.targets[0].id
                if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                else None
            )
        )
        if name in CORE:
            found.add(name)
            parts.append(ast.get_source_segment(parent, node))
    if found != CORE:
        raise ValueError("Missing pinned mechanics")
    policy = (ROOT / "experiments/majkel.py").read_text()
    code = (
        '"""Cycle 19: compact service, prompt planting and visible-demand investment.\n'
        "Own implementation informed by public Majkel1337 replays, not their source.\n"
        'Mechanics/accounting inherited from protected Unicorns Cycle 3.\n"""\n'
        "import math\nfrom collections import Counter\n\n" + "\n\n".join(parts) + "\n\n" + policy
    )
    compile(code, "<Cycle 19>", "exec")
    return code


def build(output):
    code = source()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as file:
        file.write(code)
    return sha256(code.encode()).hexdigest()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    print(build(p.parse_args().output))
