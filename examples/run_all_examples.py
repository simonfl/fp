#!/usr/bin/env python3

import re
import subprocess
import sys
import time
from pathlib import Path


EXAMPLES = [
    "baseline_family.py",
    "dual_income_nyc_family.py",
    "single_parent_public_service.py",
    "small_business_owner.py",
    "early_retiree_coastfire.py",
]


def extract_rate(output, label):
    m = re.search(rf"{label}:\s+([0-9]+(?:\.[0-9]+)?)%", output)
    return m.group(1) + "%" if m else "n/a"


def run_example(path):
    start = time.perf_counter()
    proc = subprocess.run(
        [sys.executable, str(path)],
        text=True,
        capture_output=True,
    )
    elapsed = time.perf_counter() - start
    combined = (proc.stdout or "") + (proc.stderr or "")
    return {
        "name": path.name,
        "code": proc.returncode,
        "seconds": elapsed,
        "success_rate": extract_rate(combined, "Success rate"),
        "failure_rate": extract_rate(combined, "Failure rate"),
        "output": combined,
    }


def main():
    base_dir = Path(__file__).resolve().parent
    results = []
    for name in EXAMPLES:
        results.append(run_example(base_dir / name))

    for res in results:
        print(
            f"{res['name']}: exit={res['code']} "
            f"time={res['seconds']:.2f}s "
            f"success={res['success_rate']} failure={res['failure_rate']}"
        )

    failed = [r for r in results if r["code"] != 0]
    if failed:
        print("\nFailed outputs:")
        for res in failed:
            print(f"\n--- {res['name']} ---\n{res['output'][-4000:]}")
        sys.exit(1)


if __name__ == "__main__":
    main()
