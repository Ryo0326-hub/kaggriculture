"""Build Cycle 21 from the frozen Cycle 20 source, without importing the engine."""

import argparse
import ast
from hashlib import sha256
from pathlib import Path

from scripts.make_demand_control import replace_once
from scripts.make_majkel_agent import ROOT
from scripts.make_resilience_agent import source as parent_source

PARENT_HASH = "79a8fb9661cd6fbb0c2cb9abc5a591b7daee1496b292ba8eca889f4fe6b16280"


def source():
    code = parent_source()
    if sha256(code.encode()).hexdigest() != PARENT_HASH:
        raise ValueError("Protected Cycle 20 source changed")
    code = replace_once(code, "def make_jobs(obs, ctx):", "def calendar_base_jobs(obs, ctx):")
    code = replace_once(
        code,
        "def prepare_job(job, inv, stock, p, target, ctx):",
        "def calendar_base_prepare(job, inv, stock, p, target, ctx):",
    )
    changes = (ROOT / "experiments/majkel_calendar.py").read_text()
    helpers = [
        ast.get_source_segment(changes, node)
        for node in ast.parse(changes).body
        if isinstance(node, ast.FunctionDef)
    ]
    code = replace_once(
        code,
        "def turn(obs, configuration=None):",
        "\n\n".join(helpers) + "\n\ndef turn(obs, configuration=None):",
    )
    code = replace_once(
        code,
        '    commands = [["PASS"] for _ in positions]',
        "    forced = service_assignments(\n"
        "        jobs, owner, routes, positions, carried, stock, ctx, committed\n"
        "    )\n"
        "    claimed = set(forced.values())\n"
        "    committed = {i: q for i, q in committed.items()\n"
        "                 if q not in claimed or forced.get(i) == q}\n"
        '    commands = [["PASS"] for _ in positions]',
    )
    code = replace_once(
        code,
        "            candidates = rescue_sites(jobs, p, ctx)",
        "            protected.update(q for k, q in forced.items() if k != i and q not in taken)\n"
        "            candidates = [forced[i]] if i in forced else []",
    )
    code = replace_once(
        code, "    work = life + events + 2 + fert", "    work = crop_work(c, events)"
    )
    code = replace_once(
        code,
        '            if saleable and (terminal or commands[i][0] == "PASS"'
        ' or farm["money"] < 1200):',
        "            deadline_fit = (service_fit(jobs[forced[i]], inv, stock, p, forced[i], ctx)\n"
        "                            if i in forced else None)\n"
        "            urgent = deadline_fit is not None and deadline_fit[1] <= 1\n"
        '            if saleable and not urgent and (terminal or commands[i][0] == "PASS"'
        ' or farm["money"] < 1200):',
    )
    code = replace_once(
        code,
        '"""Cycle 20: committed-supply forecasts and late-day survival rescue.',
        '"""Cycle 21: production calendars and deadline-aware crop service.',
    )
    compile(code, "<Cycle 21>", "exec")
    return code


def build(output):
    code = source()
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as file:
        file.write(code)
    return sha256(code.encode()).hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    print(build(parser.parse_args().output))
