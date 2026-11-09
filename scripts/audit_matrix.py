#!/usr/bin/env python3
"""Audit terminal matrix routes, streaming each shared XML graph only once."""
import argparse
from collections import defaultdict
import concurrent.futures
import json
from pathlib import Path
import time

from check_route import audit, batch_graph_evidence, read_trace, sha256

ROOT = Path(__file__).resolve().parents[1]


def summary(job, path, result, reused=False):
    """Keep the summary tied to full evidence, including the auditor version."""
    return {"output": job["output"], "audit": str(path), "native_state": job["state"],
            "passed": result["passed"], "inputs": result["inputs"], "graph": result["graph"],
            "route": result["route"], "routed_connection_delays": result["routed_connection_delays"],
            "errors": result["errors"][:10], "auditor_sha256": result["auditor_sha256"], "cache_reused": reused}


def check_group(item):
    graph, jobs = item
    start = time.monotonic()
    rows = []
    parsed_jobs = []
    auditor = {name: sha256(ROOT / "scripts" / name) for name in ["check_route.py", "audit_matrix.py"]}
    graph_hash = None
    for job in jobs:
        output = Path(job["output"])
        path = ROOT / "results/audits" / (output.name + ".json")
        if path.exists():
            cached = json.loads(path.read_text())
            if cached.get("auditor_sha256") == auditor:
                if graph_hash is None:
                    graph_hash = sha256(graph)
                if cached["inputs"]["rr_graph_sha256"] == graph_hash and cached["inputs"]["route_sha256"] == sha256(output / "routed.route"):
                    rows.append(summary(job, path, cached, reused=True))
                    continue
        try:
            read_trace(Path(job["output"]) / "routed.route")
            parsed_jobs.append(job)
        except ValueError as error:
            rows.append({"output": job["output"], "native_state": job["state"], "passed": False,
                         "errors": ["Invalid/incomplete route: " + str(error)]})
    if not parsed_jobs:
        return rows
    evidence = batch_graph_evidence(graph, [Path(j["output"]) / "routed.route" for j in parsed_jobs])
    for job in parsed_jobs:
        output = Path(job["output"])
        result = audit(graph, output / "routed.route", graph_evidence=evidence)
        result["auditor_sha256"] = auditor
        result["shared_graph_scan"] = {"seconds_including_routes": time.monotonic() - start, "routes": len(jobs)}
        path = ROOT / "results/audits" / (output.name + ".json")
        path.parent.mkdir(exist_ok=True)
        path.write_text(json.dumps(result, indent=2) + "\n")
        rows.append(summary(job, path, result))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", action="append", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--workers", type=int, default=2)
    args = parser.parse_args()
    groups = defaultdict(list)
    visited = set()
    for matrix in args.matrix:
        state = json.loads(matrix.read_text())
        if any(j["state"] in ("running", "queued", "waiting_preparation") for j in state["jobs"]):
            raise ValueError("Matrix is not terminal; wait for its current owner")
        for job in state["jobs"]:
            path = Path(job["output"])
            if str(path) in visited or not (path / "routed.route").exists():
                continue
            visited.add(str(path))
            manifest = json.loads((path / "manifest.json").read_text())
            graph = manifest["inputs"].get("rr_graph", {}).get("path", str(path / "rr_graph.xml"))
            groups[graph].append(job)
    rows = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as pool:
        for result in pool.map(check_group, groups.items()):
            rows.extend(result)
            args.output.write_text(json.dumps(rows, indent=2) + "\n")
            print(json.dumps({"audited": len(rows), "passed": sum(row["passed"] for row in rows)}), flush=True)
    if any(not row["passed"] and row.get("native_state") == "completed" for row in rows):
        raise RuntimeError("A native completed run failed independent audit; inspect evidence before proceeding")


if __name__ == "__main__":
    main()
