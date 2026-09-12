"""Package the unchanged, attributed public V36 agent; never run a game."""

import argparse
import ast
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "third_party/kaggriculture_v36/main.py"
SOURCE_SHA256 = "7eb5ab6c48581c82906ab6fa6b2cc5c9607513249ef59b2c45fcd6176e8653dd"


def build(output):
    content = SOURCE.read_bytes()
    if sha256(content).hexdigest() != SOURCE_SHA256:
        raise ValueError("Frozen public V36 source changed; refusing to package")
    ast.parse(content)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("xb") as stream:
        stream.write(content)
    return SOURCE_SHA256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(build(args.output))


if __name__ == "__main__":
    main()
