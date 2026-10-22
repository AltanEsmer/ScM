"""Phase-local command line for the shared frozen experiment runner."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from experiments.runner import main
if __name__ == '__main__':
    raise SystemExit(main(Path(__file__).resolve().parent))
