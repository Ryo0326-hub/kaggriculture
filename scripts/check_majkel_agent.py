"""Check isolated recorded observations. No engine imports or state advancement."""

import argparse
import json
import runpy
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from time import perf_counter

from scripts.check_growth_agent import validate


def check(source, paths):
    loaded = runpy.run_path(str(source))
    agent = loaded["agent"]
    scope = agent.__globals__
    rows = []
    max_seconds = 0
    count = 0
    for path in paths:
        raw = json.loads(path.read_text())
        cfg = raw["configuration"]
        for seat in (0, 1):
            for step, state in enumerate(raw["steps"][:-1]):
                obs = state[seat]["observation"]
                old = deepcopy(obs)
                scope["_MEMORY"].clear()  # Each callback is independent, not a game rollout.
                start = perf_counter()
                action, detail = scope["turn"](obs, cfg)
                seconds = perf_counter() - start
                try:
                    assert obs == old, "input mutation"
                    assert seconds < cfg.get("actTimeout", 1), ("timeout", seconds)
                    validate(obs, cfg, action, scope)
                except AssertionError as exc:
                    raise AssertionError((path.name, seat, step, exc.args)) from exc
                max_seconds = max(max_seconds, seconds)
                count += 1
                if step in (0, 144, 221, 264, 311, 336, 596, 696, 718):
                    rows.append(
                        dict(
                            replay=path.name,
                            seat=seat,
                            step=step,
                            seconds=seconds,
                            action=action,
                            market=detail["market"],
                        )
                    )
        print("checked", path.name, flush=True)
    return dict(
        source_sha256=sha256(Path(source).read_bytes()).hexdigest(),
        observations_checked=count,
        max_callback_seconds=max_seconds,
        method=(
            "Independent off-policy recorded-observation calls; "
            "not simulated games or competitive results."
        ),
        inputs=[dict(file=p.name, sha256=sha256(p.read_bytes()).hexdigest()) for p in paths],
        examples=rows,
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--replays", type=Path, nargs="+", required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    result = check(a.source, a.replays)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print({k: result[k] for k in ("observations_checked", "max_callback_seconds", "source_sha256")})
