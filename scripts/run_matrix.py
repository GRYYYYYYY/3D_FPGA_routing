#!/usr/bin/env python3
"""Run a finite paired routing queue from an existing preparation supervisor.

Every variant reuses the same packed netlist, placement and RRG. Preparation
failures remain eligible when all frozen inputs exist. Runs are never silently
retried. Runtime under concurrent execution is labeled as screening evidence.
Independent audits are performed separately, after routing completes.
"""

import argparse
import concurrent.futures
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared-list", required=True, type=Path)
    parser.add_argument("--variants", required=True, type=Path)
    parser.add_argument("--label", required=True)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args()
    if not args.label.replace("_", "").replace("-", "").isalnum():
        parser.error("label must be a simple filename component")
    lock = (ROOT / f"logs/{args.label}.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    lock.write(str(os.getpid()))
    lock.flush()
    variants = json.loads(args.variants.read_text())
    source = json.loads(args.prepared_list.read_text())
    queue = [{"circuit": j["circuit"], "prepared": j["output"], "variant": v["name"],
              "state": "waiting_preparation", "output": str(ROOT / f"results/runs/{args.label}_{j['circuit']}_{v['name']}")}
             for j in source["jobs"] for v in variants]
    by_variant = {v["name"]: v for v in variants}
    state = {"owner_pid": os.getpid(), "workers": args.workers, "started_epoch": time.time(),
             "timing_scope": "concurrent screening; controlled sequential repeats required",
             "prepared_list": str(args.prepared_list.resolve()), "variants": variants, "jobs": queue}
    state_path = ROOT / f"results/{args.label}.json"

    def save():
        temp = state_path.with_suffix(".tmp")
        temp.write_text(json.dumps(state, indent=2) + "\n")
        temp.replace(state_path)

    def run(job):
        output = Path(job["output"])
        manifest_path = output / "manifest.json"
        variant = by_variant[job["variant"]]
        if manifest_path.exists():
            result = json.loads(manifest_path.read_text())
            if result["status"] == "running":
                raise RuntimeError(f"Live/interrupted run requires inspection: {output}")
        else:
            command = [sys.executable, str(ROOT / "scripts/run_vpr.py"), "--reuse", job["prepared"],
                       "--binary", str(ROOT / variant["binary"]), "--output", job["output"],
                       "--timeout", str(args.timeout)]
            for key, value in variant.get("env", {}).items():
                command.extend(["--env", key + "=" + str(value)])
            if variant.get("extra"):
                command.extend(["--extra", *variant["extra"]])
            with (ROOT / f"logs/{args.label}_{job['circuit']}_{job['variant']}.log").open("w") as stream:
                subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=False)
            result = json.loads(manifest_path.read_text())
        return {"state": result["status"], "metrics": result.get("metrics", {}),
                "process_wall_seconds": result.get("process_wall_seconds"), "peak_rss_kib": result.get("peak_rss_kib")}

    save()
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending = {}
        while any(j["state"] in ("waiting_preparation", "running") for j in queue):
            preparations = {j["circuit"]: j for j in json.loads(args.prepared_list.read_text())["jobs"]}
            for job in queue:
                if len(pending) >= args.workers:
                    break
                if job["state"] != "waiting_preparation":
                    continue
                ready = preparations[job["circuit"]]
                if ready["state"] in ("queued", "running"):
                    continue
                prepared = Path(job["prepared"])
                if not (prepared / "manifest.json").exists():
                    job.update(state="unavailable_inputs", preparation_state=ready["state"])
                    continue
                manifest = json.loads((prepared / "manifest.json").read_text())
                required = ("packed.net", "fixed.place", "rr_graph.xml")
                if not all(name in manifest.get("outputs", {}) for name in required):
                    job.update(state="unavailable_inputs", preparation_state=ready["state"])
                    continue
                job["state"] = "running"
                pending[pool.submit(run, job)] = job
            save()
            if not pending:
                time.sleep(10)
                continue
            done, _ = concurrent.futures.wait(pending, timeout=10, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                job = pending.pop(future)
                try:
                    job.update(future.result())
                except Exception as error:
                    job.update(state="supervisor_error", error=str(error))
                print(json.dumps(job), flush=True)
                save()
    state["finished_epoch"] = time.time()
    save()


if __name__ == "__main__":
    main()
