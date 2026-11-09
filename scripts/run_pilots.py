#!/usr/bin/env python3
"""Sequential paired A0/A1 pilot matrix; preserve every outcome and audit."""

import json
from pathlib import Path
import subprocess
import sys

from check_route import audit, read_trace

ROOT = Path(__file__).resolve().parents[1]


def route_signature(path):
    """Ignore file headers while comparing all net/tree node and switch records."""
    return read_trace(path)


def main():
    cases = [
        ("a0", "baseline", []),
        ("off", "a1", []),
        ("w0", "a1", ["VPR_H3D_VERTICAL_WEIGHT=0", "VPR_H3D_STATS=1"]),
        ("w0p5", "a1", ["VPR_H3D_VERTICAL_WEIGHT=0.5", "VPR_H3D_STATS=1"]),
        ("w1", "a1", ["VPR_H3D_VERTICAL_WEIGHT=1", "VPR_H3D_STATS=1"]),
        ("w2", "a1", ["VPR_H3D_VERTICAL_WEIGHT=2", "VPR_H3D_STATS=1"]),
    ]
    rows = []
    for circuit in ("alu4", "ex5p", "diffeq"):
        prepared = ROOT / f"results/runs/baseline_{circuit}_w100_seed1"
        baseline_signature = None
        for label, binary, environment in cases:
            output = ROOT / f"results/runs/pilot_{circuit}_{label}"
            command = [sys.executable, str(ROOT / "scripts/run_vpr.py"), "--reuse", str(prepared),
                       "--binary", str(ROOT / f"artifacts/bin/{binary}/vpr"), "--output", str(output)]
            for entry in environment:
                command.extend(["--env", entry])
            # Resume only runs that already have a terminal manifest; never
            # overwrite or silently use interrupted/unfinished runs.
            if (output / "manifest.json").exists():
                manifest = json.loads((output / "manifest.json").read_text())
                if manifest["status"] == "running":
                    raise RuntimeError(f"Unfinished run needs inspection: {output}")
            else:
                subprocess.run(command, check=False)
                manifest = json.loads((output / "manifest.json").read_text())
            row = {"circuit": circuit, "variant": label, "manifest": str(output / "manifest.json"),
                   "status": manifest["status"], "metrics": manifest["metrics"],
                   "process_wall_seconds": manifest["process_wall_seconds"], "peak_rss_kib": manifest["peak_rss_kib"]}
            if (output / "routed.route").exists():
                check_path = ROOT / f"results/pilot_{circuit}_{label}.audit.json"
                if check_path.exists():
                    checked = json.loads(check_path.read_text())
                else:
                    checked = audit(prepared / "rr_graph.xml", output / "routed.route")
                    check_path.write_text(json.dumps(checked, indent=2) + "\n")
                row["audit_passed"] = checked["passed"]
                row["route"] = checked["route"]
                if label == "a0":
                    baseline_signature = route_signature(output / "routed.route")
                if label in ("off", "w0"):
                    row["matches_unmodified_route"] = baseline_signature == route_signature(output / "routed.route")
                    if not row["matches_unmodified_route"]:
                        raise RuntimeError(f"Disabled-mode equivalence failed: {output}")
            rows.append(row)
            (ROOT / "results/a1_pilots.json").write_text(json.dumps(rows, indent=2) + "\n")
            print(json.dumps(row), flush=True)


if __name__ == "__main__":
    main()
