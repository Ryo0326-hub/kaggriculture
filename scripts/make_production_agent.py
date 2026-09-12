"""Build Cycle 18 from the hash-checked Cycle 17 descendant of Cycle 15."""

import argparse
import ast
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.make_carrot_control import edit_function
from scripts.make_demand_control import ROOT, replace_once
from scripts.make_growth_agent import build as build_parent

PARENT_SHA256 = "96297a3e899d77bbb5f0ec0299da34418bbdf9c62d999738df39da7a4237c6ea"


def build(output):
    with TemporaryDirectory() as directory:
        parent = Path(directory) / "main.py"
        build_parent(parent)
        code = parent.read_text()
    if sha256(code.encode()).hexdigest() != PARENT_SHA256:
        raise ValueError("Frozen Cycle 17 changed")
    code = edit_function(
        code,
        "growth_jobs",
        "(not harvest or bonus_water)",
        '(spec["interval"] or not harvest or bonus_water)',
    )
    code = edit_function(
        code,
        "growth_investment",
        '    room = cfg.get("shedCapacity", 100) - sum(planned["private"]["shed"].values())',
        '    room = cfg.get("shedCapacity", 100) - sum(planned["private"]["shed"].values())\n'
        '    room -= sum(sum(inv.values()) for inv in planned["private"]["inventories"])',
    )
    helpers = (ROOT / "experiments/production.py").read_text()
    first = next(n for n in ast.parse(helpers).body if isinstance(n, ast.FunctionDef))
    line = min([first.lineno, *(n.lineno for n in first.decorator_list)])
    helpers = "\n".join(helpers.splitlines()[line - 1 :])
    code = replace_once(
        code,
        "def agent(obs, configuration=None):\n    return growth_turn(obs, configuration)[0]",
        helpers + "\n\ngrowth_routes = production_routes\n\ndef agent(obs, configuration=None):\n"
        "    return production_turn(obs, configuration)[0]",
    )
    compile(code, "<Cycle 18 production>", "exec")
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
