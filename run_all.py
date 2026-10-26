"""Воспроизвести подготовку данных, EDA и диаграммы одной командой."""
from pathlib import Path
import subprocess
import sys


def main():
    root = Path(__file__).resolve().parent
    for name in ("split_data.py", "eda.py", "diagrams.py"):
        subprocess.run([sys.executable, str(root / "scripts" / name)],
                       cwd=root, check=True)
    from scripts.eda import artifact_inventory
    artifact_inventory()


if __name__ == "__main__":
    main()
