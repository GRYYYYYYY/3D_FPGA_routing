#!/usr/bin/env python3
"""Join frozen run manifests, native counters and independent audit evidence.

Failed/time-limited routes remain rows, but only jointly successful, checked
pairs enter QoR ratios. A final collection rejects unfinished matrices and any
native successful route without a matching independent audit.
"""
import argparse
from collections import Counter, defaultdict
import csv
import datetime
import json
import math
from pathlib import Path
import re
import statistics

ROOT = Path(__file__).resolve().parents[1]
MATRICES = ["koios_a0a4_seed1", "koios_controls_seed1", "koios_prune_controls",
            "sweep_all_v4", "paired_seeds_all", "natural_seeds_all", "small_prune_controls",
            "tuning", "tuned_heldout", "elliptic_w160_all", "controlled_timing"]
METRICS = ["critical_path_ns", "wirelength", "vertical_channels", "router_seconds",
           "process_wall_seconds", "peak_rss_kib", "heap_pushes", "heap_pops",
           "routed_delay_remote_mean_ns"]
COMPARISONS = [("a1_w2", "a3"), ("a2", "a3"), ("a1_w2_prune", "a3_prune"),
               ("a0", "a0_prune"), ("a0_prune", "a4_subtree"),
               ("a1_w2_prune", "a4_subtree"), ("a3_prune", "a4_subtree"),
               ("a3", "a4_subtree"), ("a1_tuned", "a3_tuned"),
               ("a1_tuned", "a4_tuned"), ("a3_tuned", "a4_tuned"),
               ("a0_prune", "a4_tuned"), ("a0", "a0_instrumented"),
               ("a0_instrumented", "a3"), ("a0_instrumented", "a4_subtree"),
               ("a1_w2", "a3_tuned"), ("a1_w2", "a4_tuned")]


def native_counters(text):
    """Derive counters from immutable logs without modifying run manifests."""
    result = {}
    totals = re.findall(r"Router Stats: total_nets_routed: (\d+) total_connections_routed: (\d+) total_heap_pushes: (\d+) total_heap_pops: (\d+)", text)
    if totals:
        result.update(zip(["nets_routed", "connections_routed", "heap_pushes", "heap_pops"], map(int, totals[-1])))
    search = re.findall(r"Time spent on path search: ([\d.eE+-]+) seconds", text)
    if search:
        result["path_search_seconds"] = float(search[-1])
    prefixes = {"H3D_PLAN": "planning", "H3D_TREE": "tree", "H3D_SCC": "scc", "H3D_CONTROL": "control"}
    for prefix, label in prefixes.items():
        lines = re.findall(r"^" + prefix + r" (.*)$", text, re.M)
        if lines:
            for key, value in re.findall(r"(\w+)=([\d.eE+-]+)(?:\s|$)", lines[-1]):
                result[label + "_" + key] = float(value) if any(c in value for c in ".eE") else int(value)
    iterations = []
    pattern = r"^\s*(\d+)\s+([\d.eE+-]+)\s+([\d.eE+-]+)\s+(\d+)\s+([\d.eE+-]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+\(\s*[\d.]+%\)\s+(\d+)\s+\(\s*[\d.]+%\)\s+([\d.eE+-]+)"
    for match in re.finditer(pattern, text, re.M):
        values = match.groups()
        iterations.append(dict(zip(["iteration", "seconds", "pres_fac", "bbox_updates", "heap_pushes", "nets_routed", "connections_routed", "overused_resources", "wirelength", "critical_path_ns"],
                                   [int(values[0]), float(values[1]), float(values[2]),
                                    *[int(float(v)) for v in values[3:9]], float(values[9])])))
    if iterations:
        result["last_iteration"] = iterations[-1]["iteration"]
        result["last_overused_resources"] = iterations[-1]["overused_resources"]
    failure = re.findall(r"^Routing aborted.*$", text, re.M)
    if failure:
        result["native_abort_reason"] = failure[-1]
    elif "Routing failed." in text:
        result["native_failure_reason"] = "Routing failed."
        if iterations:
            result["native_failure_reason"] += f" Last reported iteration {iterations[-1]['iteration']}, overused resources {iterations[-1]['overused_resources']}."
    return result, iterations


def dataset(matrix, circuit):
    if matrix.startswith("koios_"):
        return "native20_w100"
    if matrix == "sweep_all_v4" or (matrix == "small_prune_controls" and "_seed" not in circuit):
        return "architecture_sweep"
    if matrix == "elliptic_w160_all":
        return "elliptic_w160"
    if matrix == "tuning":
        return "training_parameters"
    if matrix == "controlled_timing":
        return "sequential_timing"
    return "paired_seeds_w100"


def geomean(values):
    return math.exp(statistics.mean(math.log(v) for v in values)) if values else None


def compare(cases, baseline, treatment):
    """Compare only the identical jointly legal cases, reducing repeats first."""
    matched = {}
    for case, data in cases.items():
        if baseline not in data or treatment not in data:
            continue
        a, b = data[baseline], data[treatment]
        if not all(r["valid_solution"] for r in [*a, *b]):
            continue
        ratios = {}
        for metric in METRICS:
            if all(r["metrics"].get(metric) is not None for r in [*a, *b]):
                denominator = statistics.median(r["metrics"][metric] for r in a)
                numerator = statistics.median(r["metrics"][metric] for r in b)
                if denominator > 0 and numerator > 0:
                    ratios[metric] = numerator / denominator
        matched[case] = ratios
    summary = {}
    for metric in METRICS:
        values = [ratios[metric] for ratios in matched.values() if metric in ratios]
        if values:
            summary[metric] = {"geomean": geomean(values), "cases": len(values),
                               "minimum": min(values), "maximum": max(values)}
    return {"baseline": baseline, "treatment": treatment, "paired_cases": len(matched),
            "ratios": summary, "case_ratios": matched}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-incomplete", action="store_true", help="Write an explicitly provisional collection")
    args = parser.parse_args()
    rows, missing, omitted, convergence = [], [], [], []
    audit_index = {}
    for path in sorted((ROOT / "results").glob("audits_*.json"), key=lambda p: p.stat().st_mtime):
        for record in json.loads(path.read_text()):
            audit_index[record["output"]] = record
    paired_inputs = defaultdict(set)
    for name in MATRICES:
        state_path = ROOT / f"results/{name}.json"
        if not state_path.exists():
            missing.append(name)
            continue
        state = json.loads(state_path.read_text())
        if "finished_epoch" not in state:
            missing.append(name)
        for job in state["jobs"]:
            if job["state"] in ("running", "waiting_preparation", "queued"):
                continue
            output = Path(job["output"])
            manifest_path = output / "manifest.json"
            if not manifest_path.exists():
                # Historical placeholder failures in the initial seed queue are
                # superseded by the explicit natural_seeds_all queue, not counted twice.
                omitted.append({"matrix": name, "circuit": job["circuit"], "variant": job["variant"], "state": job["state"]})
                if not (name == "paired_seeds_all" and job["circuit"].startswith("elliptic_seed")
                        and job["state"] == "unavailable_inputs"):
                    missing.append(str(output) + ": missing run manifest")
                continue
            manifest = json.loads(manifest_path.read_text())
            group = dataset(name, job["circuit"])
            fingerprint = tuple(manifest["inputs"][key]["sha256"] for key in ("architecture", "packed_netlist", "placement", "rr_graph"))
            paired_inputs[(group, job["circuit"])].add(fingerprint)
            metrics = dict(manifest["metrics"])
            counters, history = native_counters((output / "vpr.log").read_text(errors="replace"))
            metrics.update(counters)
            metrics.update(process_wall_seconds=manifest.get("process_wall_seconds"), peak_rss_kib=manifest.get("peak_rss_kib"))
            checked = audit_index.get(str(output))
            # Older summaries did not include input hashes/delays; use their
            # current detailed evidence rather than silently trusting a pathname.
            if checked and ("inputs" not in checked or "routed_connection_delays" not in checked) and checked.get("audit"):
                checked = json.loads(Path(checked["audit"]).read_text())
            native_ok = manifest["status"] == "completed" and metrics.get("native_full_check_passed") and metrics.get("routing_success_reported")
            audit_ok = bool(checked and checked["passed"])
            if audit_ok:
                if checked["inputs"]["rr_graph_sha256"] != manifest["inputs"]["rr_graph"]["sha256"] or checked["inputs"]["route_sha256"] != manifest["outputs"]["routed.route"]["sha256"]:
                    raise RuntimeError(f"Audit/run hash mismatch: {output}")
                metrics.update(vertical_channels=checked["route"]["unique_used_vertical_channels"],
                               vertical_net_occupancy=checked["route"]["vertical_channel_net_occupancy"],
                               cross_layer_sink_connections=checked["route"]["cross_layer_sink_connections"])
                delay = checked.get("routed_connection_delays", {})
                if delay.get("available"):
                    for scope in ["all", "remote"]:
                        for key, value in (delay.get(scope) or {}).items():
                            metrics["routed_delay_" + scope + "_" + key] = value
            if native_ok and not audit_ok:
                missing.append(str(output) + ": independent audit")
            row = {"dataset": group, "circuit": job["circuit"], "variant": job["variant"], "repeat": job.get("repeat"),
                   "matrix": name, "output": str(output), "status": manifest["status"], "native_success": bool(native_ok),
                   "returncode": manifest.get("returncode"), "timeout_seconds": manifest.get("timeout_seconds"),
                   "independent_audit_passed": audit_ok, "valid_solution": bool(native_ok and audit_ok),
                   "paired_input_hashes": fingerprint, "binary_sha256": manifest["inputs"]["binary"]["sha256"],
                   "environment": manifest["experimental_environment"], "metrics": metrics}
            if checked:
                row["graph"] = checked.get("graph", {})
            rows.append(row)
            convergence.extend({"dataset": group, "circuit": job["circuit"], "variant": job["variant"], "repeat": job.get("repeat"), **entry} for entry in history)
    inconsistent = [key for key, fingerprints in paired_inputs.items() if len(fingerprints) != 1]
    if inconsistent:
        raise RuntimeError(f"Paired architecture/packing/placement/RRG changed: {inconsistent}")
    if missing and not args.allow_incomplete:
        raise RuntimeError(f"Final evidence is incomplete: {missing[:12]}")
    # Repeats are reduced within a case before ratios; architectures and seeds
    # remain explicit cases, not falsely treated as independent circuit samples.
    by_case = defaultdict(lambda: defaultdict(list))
    for row in rows:
        by_case[(row["dataset"], row["circuit"])][row["variant"]].append(row)
    summaries = []
    comparisons = []
    for group in sorted({r["dataset"] for r in rows}):
        variants = sorted({r["variant"] for r in rows if r["dataset"] == group})
        cases = {c: data for (g, c), data in by_case.items() if g == group}
        for baseline, treatment in COMPARISONS:
            if baseline == "a1_w2" and treatment.endswith("_tuned") and "a1_tuned" in variants:
                continue  # The identical selected A1 setting has its own label here.
            comparison = compare(cases, baseline, treatment)
            if comparison["paired_cases"]:
                comparisons.append({"dataset": group, **comparison})
        for variant in variants:
            selected = [r for r in rows if r["dataset"] == group and r["variant"] == variant]
            entry = {"dataset": group, "variant": variant, "runs": len(selected), "statuses": dict(Counter(r["status"] for r in selected)),
                     "valid_solutions": sum(r["valid_solution"] for r in selected), "paired_cases": 0, "ratios_to_a0": {}}
            pairs = []
            for case, data in cases.items():
                if variant not in data or "a0" not in data:
                    continue
                a, b = data["a0"], data[variant]
                if not all(r["valid_solution"] for r in [*a, *b]):
                    continue
                pairs.append((a, b))
            entry["paired_cases"] = len(pairs)
            for metric in METRICS:
                ratios = []
                for a, b in pairs:
                    if all(r["metrics"].get(metric) is not None for r in [*a, *b]):
                        denominator = statistics.median(r["metrics"][metric] for r in a)
                        numerator = statistics.median(r["metrics"][metric] for r in b)
                        if denominator > 0 and numerator > 0:
                            ratios.append(numerator / denominator)
                if ratios:
                    entry["ratios_to_a0"][metric] = {"geomean": geomean(ratios), "cases": len(ratios), "minimum": min(ratios), "maximum": max(ratios)}
            summaries.append(entry)
    document = {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "provisional": bool(missing), "missing": missing,
                "paired_inputs_verified": True, "omitted_placeholder_jobs": omitted,
                "timing_scope": "Only sequential_timing has repeated runs after our queues; other times are concurrent screening measurements",
                "iteration_counter_scope": "Iteration heap counts are rounded in native logs; final Router Stats totals retain integer precision",
                "rows": rows, "summaries": summaries, "comparisons": comparisons}
    (ROOT / "results/analysis.json").write_text(json.dumps(document, indent=2) + "\n")
    flat = [{key: row[key] for key in ["dataset", "circuit", "variant", "repeat", "status", "returncode", "timeout_seconds", "valid_solution", "output"]} | row["metrics"] for row in rows]
    fields = list(dict.fromkeys(key for row in flat for key in row))
    with (ROOT / "results/analysis.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(flat)
    (ROOT / "results/convergence.json").write_text(json.dumps(convergence, indent=2) + "\n")
    print(json.dumps({"runs": len(rows), "valid_solutions": sum(r["valid_solution"] for r in rows), "provisional": bool(missing), "missing_items": len(missing)}))


if __name__ == "__main__":
    main()
