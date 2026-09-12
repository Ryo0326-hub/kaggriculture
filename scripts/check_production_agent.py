"""Check fixed server observations without running a game or applying actions."""

import argparse
import ast
import json
import runpy
import sys
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from time import perf_counter

from scripts.check_growth_agent import validate

STEPS = (0, 72, 179, 244, 290, 340, 362, 428, 456, 480, 503, 696, 714, 718)


def check(source, paths):
    code = source.read_text()
    imports = {
        n.module.split(".")[0] if isinstance(n, ast.ImportFrom) else a.name.split(".")[0]
        for n in ast.walk(ast.parse(code))
        if isinstance(n, (ast.Import, ast.ImportFrom))
        for a in n.names
    }
    assert imports <= sys.stdlib_module_names, imports - sys.stdlib_module_names
    start = perf_counter()
    scope = runpy.run_path(str(source))
    startup = perf_counter() - start
    assert [k for k, v in scope.items() if callable(v)][-1] == "agent"
    scope = scope["agent"].__globals__
    rows, inputs = [], []
    for path in paths:
        replay = json.loads(path.read_text())
        cfg = replay["configuration"]
        inputs.append(dict(file=path.name, sha256=sha256(path.read_bytes()).hexdigest()))
        for seat in (0, 1):
            for step in STEPS:
                obs = deepcopy(replay["steps"][step][seat]["observation"])
                obs["step"] = step
                original = deepcopy(obs)
                scope["growth_routes"].cache_clear()
                start = perf_counter()
                action, detail = scope["production_turn"](obs, cfg)
                elapsed = perf_counter() - start
                assert obs == original, (path.name, seat, step, "observation mutated")
                validate(obs, cfg, action, scope)
                assert elapsed < cfg.get("actTimeout", 1), (path.name, seat, step, elapsed)
                rows.append(
                    dict(
                        replay=path.name,
                        seat=seat,
                        step=step,
                        seconds=elapsed,
                        workers=detail["daily"]["workers"],
                        assignment_count=len(detail["dispatch"]["assigned"]),
                        fertilizer=detail["fertilizer_reserve"],
                        feed=detail["feed_reserve"],
                        investment=detail["investment"].get("chosen"),
                        action=action,
                    )
                )
    return dict(
        method="Independent recorded observations; preconditions and inventory arithmetic only. "
        "No game engine import, action application, simulation, training "
        "or counterfactual continuation.",
        source_sha256=sha256(source.read_bytes()).hexdigest(),
        imports=sorted(imports),
        startup_seconds=startup,
        decisions=len(rows),
        max_seconds=max(r["seconds"] for r in rows),
        inputs=inputs,
        checks=rows,
        server_validation="pending",
        competitive_performance="unmeasured",
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("replays", nargs="+", type=Path)
    args = parser.parse_args()
    report = check(args.source, args.replays)
    with args.output.open("x") as file:
        file.write(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("inputs", "checks")}, indent=2))


if __name__ == "__main__":
    main()
