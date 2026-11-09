#!/usr/bin/env python3
"""Check that timing repetitions compare the same deterministic route quality."""
from collections import defaultdict
import json
from pathlib import Path

from check_route import read_trace, sha256

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT / "results/controlled_timing.json"
    state = json.loads(source.read_text())
    protocol = json.loads((ROOT / "configs/timing_protocol.json").read_text())
    assert "finished_epoch" in state
    assert len(state["jobs"]) == protocol["total_runs"]
    groups = defaultdict(list)
    for job in state["jobs"]:
        assert job["state"] == "completed", job
        groups[job["circuit"], job["variant"]].append(job)
    assert len(groups) == len(protocol["cases"]) * protocol["settings"]
    results = []
    for (case, variant), jobs in sorted(groups.items()):
        assert sorted(j["repeat"] for j in jobs) == list(range(1, protocol["repetitions"] + 1))
        manifests = [json.loads((Path(j["output"]) / "manifest.json").read_text()) for j in jobs]
        hashes = [m["outputs"]["routed.route"]["sha256"] for m in manifests]
        byte_equal = len(set(hashes)) == 1
        semantic_equal = byte_equal
        if not byte_equal:
            traces = [read_trace(Path(j["output"]) / "routed.route") for j in jobs]
            semantic_equal = all(t == traces[0] for t in traces)
        quality_equal = all(len({j["metrics"][metric] for j in jobs}) == 1 for metric in ["critical_path_ns", "wirelength"])
        results.append({"circuit": case, "variant": variant, "repetitions": len(jobs),
                        "byte_equal": byte_equal, "semantic_route_equal": semantic_equal,
                        "cpd_wirelength_equal": quality_equal, "route_sha256": hashes})
    document = {"passed": all(r["semantic_route_equal"] and r["cpd_wirelength_equal"] for r in results),
                "matrix_sha256": sha256(source), "cases": results}
    (ROOT / "results/timing_repeat_determinism.json").write_text(json.dumps(document, indent=2) + "\n")
    print(json.dumps({"passed": document["passed"], "groups": len(results),
                      "byte_identical_groups": sum(r["byte_equal"] for r in results)}))
    assert document["passed"], "Inspect changed routes/quality before interpreting timing"


if __name__ == "__main__":
    main()
