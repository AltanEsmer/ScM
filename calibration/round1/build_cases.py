"""Rebuild the frozen calibration case artifact from curated pool modules."""
import json
from pathlib import Path
from pool_algorithms import make_tasks as algorithms
from pool_semantics import make_tasks as semantics


def make_tasks():
    return algorithms() + semantics()


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    (root / 'tasks.json').write_text(json.dumps(make_tasks(), indent=2) + '\n')
