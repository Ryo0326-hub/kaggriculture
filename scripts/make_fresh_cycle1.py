"""Package only the independently written source; never imports another agent."""

import argparse
import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "experiments/fresh_cycle1.py"


def build(output):
    source = SOURCE.read_bytes()
    tree = ast.parse(source)
    imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
    assert len(imports) == 1 and isinstance(imports[0], ast.Import)
    assert [a.name for a in imports[0].names] == ["math"]
    assert isinstance(tree.body[-1], ast.FunctionDef) and tree.body[-1].name == "agent"
    compile(source, "main.py", "exec")
    output = Path(output)
    if output.exists():
        raise FileExistsError(f"Refusing to replace existing artifact: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as handle:
        handle.write(source)
    return hashlib.sha256(source).hexdigest()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(build(args.output))
