"""Build Cycle 15 from frozen Cycle 13 without running games or modifying parents."""

# Replacement literals intentionally match the frozen source's formatting.
# ruff: noqa: E501

import argparse
import ast
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from scripts.make_carrot_control import edit_function
from scripts.make_demand_control import ROOT, replace_once
from scripts.make_throughput_agent import build as build_throughput

CYCLE13_SHA256 = "542547dbe7cd63856b2a6f037e2014790c1410316c3b3872f67ea85c2b628947"


def build(output):
    with TemporaryDirectory() as temporary:
        parent = Path(temporary) / "main.py"
        build_throughput(parent)
        code = parent.read_text()
    if sha256(code.encode()).hexdigest() != CYCLE13_SHA256:
        raise ValueError("Cycle 13 source changed")

    code = edit_function(
        code,
        "mixed_turn",
        '    commands = [action["farmer"], *action["hands"]]',
        """    commands = [action["farmer"], *action["hands"]]
    # Terminal return is a hard constraint, reserved before every crop/input job.
    terminal_returns = {
        i for i, p in enumerate(positions)
        if day == final and sum(private["inventories"][i].values())
        and remaining <= min(distance(p, a) for a in access) + 2
    }
    for i in terminal_returns:
        p = positions[i]
        shed = min(access, key=lambda a: (distance(p, a), a))
        commands[i] = move_toward(p, shed) if p != shed else ["DROP"]""",
    )
    for before, after in (
        (
            "        if done and not any(inv.get(a, 0) for a in ANIMALS):",
            "        if done and i not in terminal_returns and not any(inv.get(a, 0) for a in ANIMALS):",
        ),
        (
            '        if not expansion or not isinstance(tile, dict) or tile.get("placed_day") != day:',
            '        if i in terminal_returns or not expansion or not isinstance(tile, dict) or tile.get("placed_day") != day:',
        ),
        (
            '            and tile["planted_day"] == day',
            '            and day < final and i not in terminal_returns\n            and tile["planted_day"] == day',
        ),
        (
            "                i in urgent_assignments\n",
            "                i in terminal_returns\n                or i in urgent_assignments\n",
        ),
        (
            '            steps = 2 if job[0] == "WATER" else 1\n'
            "            if distance(positions[i], site) + steps + allowance <= remaining:\n"
            "                candidates.append((distance(positions[i], site), i))",
            """            delivery = min(distance(site, a) for a in access) + 1
            candidate_job = repaired_terminal_job(
                tile, job, day, final, remaining, distance(positions[i], site), delivery)
            if not candidate_job:
                continue
            steps = candidate_job[2]
            if expansion and day == final:
                allowance = delivery
            if distance(positions[i], site) + steps + allowance <= remaining:
                candidates.append((distance(positions[i], site), i, candidate_job[0]))""",
        ),
        (
            "            urgent_pairs.extend((travel, site, i, job[0]) for travel, i in candidates)",
            "            urgent_pairs.extend((travel, site, i, op) for travel, i, op in candidates)",
        ),
        (
            "            _, i = min(candidates)\n            urgent_assignments[i] = (site, job[0])",
            "            _, i, op = min(candidates)\n            urgent_assignments[i] = (site, op)",
        ),
        (
            "            op, urgency, steps = job\n",
            """            job = repaired_terminal_job(
                tile, job, day, final, remaining, distance(p, site),
                min(distance(site, a) for a in access) + 1)
            if not job:
                continue
            op, urgency, steps = job
""",
        ),
        (
            '                if op == "HARVEST" and day == final\n',
            '                if op in ("HARVEST", "WATER") and day == final\n',
        ),
        (
            '            if site in fertile and op in ("WATER", "FERTILIZE"):',
            '            if day < final and site in fertile and op in ("WATER", "FERTILIZE"):',
        ),
        (
            '        "active_crops": len(plants),',
            '        "terminal_returns": sorted(terminal_returns),\n        "active_crops": len(plants),',
        ),
    ):
        code = edit_function(code, "mixed_turn", before, after)
    start = code.index("    wages = work = 0\n", code.index("def throughput_value("))
    end = code.index("    # Retain 75%", start)
    code = (
        code[:start]
        + ("    wages, work, feasible, _, _ = repaired_labor_delta(obs, cfg, assets, additions)\n")
        + code[end:]
    )
    helpers = (ROOT / "experiments/repairs.py").read_text()
    first = next(n for n in ast.parse(helpers).body if isinstance(n, ast.FunctionDef))
    helpers = "\n".join(helpers.splitlines()[first.lineno - 1 :])
    bindings = """
crop_job = repaired_crop_job
crop_column = repaired_column
throughput_assets = repaired_assets
throughput_staff = repaired_staff
throughput_investment = repaired_investment
expansion_investment = repaired_investment
"""
    code = replace_once(
        code,
        "def agent(obs, configuration=None):",
        helpers + "\n\n" + bindings + "\n\ndef agent(obs, configuration=None):",
    )
    compile(code, "<Cycle 15 repairs>", "exec")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as file:
        file.write(code)
    return sha256(code.encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    print(build(args.output))


if __name__ == "__main__":
    main()
