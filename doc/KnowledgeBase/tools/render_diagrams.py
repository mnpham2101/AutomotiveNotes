#!/usr/bin/env python3
"""Render every PlantUML (.puml) source under md/diagrams/ into an .svg next to it.

Requires a JRE on PATH (`java`). Uses the vendored tools/plantuml.jar so no
network access is needed at build time.
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIAGRAMS_DIR = ROOT / "md" / "diagrams"
PLANTUML_JAR = Path(__file__).resolve().parent / "plantuml.jar"


def main() -> int:
    if shutil.which("java") is None:
        print("ERROR: java not found on PATH. A JRE is required to render PlantUML diagrams.", file=sys.stderr)
        return 1

    puml_files = sorted(DIAGRAMS_DIR.glob("*.puml"))
    if not puml_files:
        print(f"No .puml files found under {DIAGRAMS_DIR}")
        return 0

    failures = []
    for puml in puml_files:
        print(f"Rendering {puml.name} -> svg")
        result = subprocess.run(
            ["java", "-jar", str(PLANTUML_JAR), "-tsvg", str(puml)],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            failures.append(puml.name)
            print(result.stdout)
            print(result.stderr, file=sys.stderr)

    if failures:
        print(f"FAILED to render: {', '.join(failures)}", file=sys.stderr)
        return 1

    print(f"Rendered {len(puml_files)} diagram(s) successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
