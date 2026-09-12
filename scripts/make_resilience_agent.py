"""Build Cycle 20 from hash-checked Cycle 19; never imports the game engine."""

import argparse
import ast
from hashlib import sha256
from pathlib import Path

from scripts.make_demand_control import replace_once
from scripts.make_majkel_agent import ROOT
from scripts.make_majkel_agent import source as parent_source

PARENT_HASH = "eb151fe1e088e598edfdcd6b10c5c108bdb91783bfbbac9758211b5df29bd17d"


def source():
    code = parent_source()
    if sha256(code.encode()).hexdigest() != PARENT_HASH:
        raise ValueError("Protected Cycle 19 source changed")
    changes = (ROOT / "experiments/majkel_resilience.py").read_text()
    nodes = {n.name: n for n in ast.parse(code).body if isinstance(n, ast.FunctionDef)}
    helpers = []
    for node in ast.parse(changes).body:
        if not isinstance(node, ast.FunctionDef):
            continue
        body = ast.get_source_segment(changes, node)
        if node.name in nodes:
            code = replace_once(
                code, ast.get_source_segment(parent_source(), nodes[node.name]), body
            )
        else:
            helpers.append(body)
    code = replace_once(
        code,
        "def turn(obs, configuration=None):",
        "\n\n".join(helpers) + "\n\ndef turn(obs, configuration=None):",
    )
    code = replace_once(
        code, "            candidates = []", "            candidates = rescue_sites(jobs, p, ctx)"
    )
    code = replace_once(
        code,
        '    ops = [list(o) for o in job["ops"]]',
        '    ops = [list(o) for o in job["ops"]]\n'
        '    if ctx["day"] < ctx["final"] and ctx["remaining"] <= 6 and job["urgency"] >= 5:\n'
        '        essential = [o for o in ops if o[0] in ("FEED", "WATER")]\n'
        "        if essential:\n"
        "            ops = essential",
    )
    code = replace_once(
        code,
        '"""Cycle 19: compact service, prompt planting and visible-demand investment.',
        '"""Cycle 20: committed-supply forecasts and late-day survival rescue.',
    )
    compile(code, "<Cycle 20>", "exec")
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
