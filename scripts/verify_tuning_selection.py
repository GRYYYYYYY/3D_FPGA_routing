#!/usr/bin/env python3
"""Recompute the archived exploratory selection; never choose new parameters."""
from collections import defaultdict
import json
import math
from pathlib import Path

from check_route import sha256

ROOT = Path(__file__).resolve().parents[1]


def main():
    matrix = ROOT / "results/tuning.json"
    protocol = ROOT / "configs/tuning_protocol.json"
    selected_path = ROOT / "results/tuning_selection.json"
    state = json.loads(matrix.read_text())
    assert "finished_epoch" in state
    cases = defaultdict(dict)
    for job in state["jobs"]:
        cases[job["circuit"]][job["variant"]] = job
    assert len(cases) == 2
    variants = [v["name"] for v in json.loads(protocol.read_text())["parameters"]]
    scores = {}
    for variant in variants:
        cpd, wirelength, eligible = [], [], True
        for jobs in cases.values():
            job, baseline = jobs[variant], jobs["a0"]
            for record in [job, baseline]:
                eligible &= record["state"] == "completed" and record["metrics"]["native_full_check_passed"]
            cpd.append(job["metrics"]["critical_path_ns"] / baseline["metrics"]["critical_path_ns"])
            wirelength.append(job["metrics"]["wirelength"] / baseline["metrics"]["wirelength"])
        eligible &= all(value <= 1.05 for value in wirelength)
        scores[variant] = {"cpd_ratio": math.prod(cpd) ** .5, "wirelength_ratio": math.prod(wirelength) ** .5,
                           "eligible": bool(eligible)}
    recomputed = {}
    archived = json.loads(selected_path.read_text())
    for family in ["a1", "a3", "a4"]:
        choices = [v for v in variants if v.startswith(family + "_") and scores[v]["eligible"]]
        best = min(choices, key=lambda v: (scores[v]["cpd_ratio"], scores[v]["wirelength_ratio"], variants.index(v)))
        assert best == archived["selected"][family]["variant"]
        for metric in ["cpd_ratio", "wirelength_ratio"]:
            assert math.isclose(scores[best][metric], archived["selected"][family][metric], rel_tol=1e-12)
        recomputed[family] = {"variant": best, **scores[best]}
    result = {"passed": True, "selected": recomputed,
              "inputs": {str(p.relative_to(ROOT)): sha256(p) for p in [matrix, protocol, selected_path]},
              "scope": "Verification of the already selected two-case exploratory protocol; no reselection using held-out or timing results"}
    (ROOT / "results/tuning_reproduction_check.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
