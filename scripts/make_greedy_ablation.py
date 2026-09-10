"""Create a self-contained control changing only the assignment algorithm."""

import argparse
from pathlib import Path

GREEDY = """

def greedy_assignment(weights, seed_tasks, seed_budget):
    used = set()
    selected = []
    for row in weights:
        options = [j for j, score in enumerate(row)
                   if score is not None and score > 0 and j not in used
                   and (not seed_tasks[j] or seed_budget > 0)]
        if not options:
            selected.append(-1)
            continue
        j = max(options, key=lambda j: row[j])
        selected.append(j)
        used.add(j)
        seed_budget -= int(seed_tasks[j])
    return tuple(selected)


def agent(obs, configuration=None):
    return plan_turn(obs, configuration, allocator=greedy_assignment)[0]
"""


def build(source, output):
    code = Path(source).read_text()
    # Kaggle selects the last callable in namespace insertion order. Redefining an
    # existing agent name does not move it after a newly introduced helper.
    if code.count("\ndef agent(") != 1:
        raise ValueError("Expected one final agent entry point")
    prefix = code.rsplit("\ndef agent(", 1)[0]
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as artifact:
        artifact.write(prefix + GREEDY)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("baselines/step_2.py"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.source, args.output)
    print(args.output)


if __name__ == "__main__":
    main()
