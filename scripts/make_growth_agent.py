"""Build the Cycle 17 custom growth candidate from immutable Cycle 15."""

import argparse
import ast
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.make_demand_control import ROOT, replace_once
from scripts.make_repaired_agent import build as build_parent

PARENT_SHA256 = "ce4444126f5ef7e0ee01a22f395ae87ee442ec2f329c4feb6aedf0687af45f1a"


def build(output):
    with TemporaryDirectory() as directory:
        path = Path(directory) / "main.py"
        build_parent(path)
        code = path.read_text()
    if sha256(code.encode()).hexdigest() != PARENT_SHA256:
        raise ValueError("Frozen Cycle 15 has changed")
    helpers = (ROOT / "experiments/growth.py").read_text()
    first = next(n for n in ast.parse(helpers).body if isinstance(n, ast.FunctionDef))
    helpers = "\n".join(helpers.splitlines()[first.lineno - 1 :])
    code = replace_once(
        code,
        "def agent(obs, configuration=None):\n"
        "    return expansion_turn(obs, configuration, timing=1)[0]",
        helpers
        + "\n\nfarm_sites = growth_sites\n\n"
        + "def agent(obs, configuration=None):\n    return growth_turn(obs, configuration)[0]",
    )
    compile(code, "<Cycle 17 growth>", "exec")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as file:
        file.write(code)
    return sha256(code.encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(build(parser.parse_args().output))


if __name__ == "__main__":
    main()
