#!/usr/bin/env python3
"""Prepare the pinned 20-circuit set with one persistent, bounded CPU queue.

Preparation runtime is not a controlled router comparison. Paired routing runs
reuse these frozen outputs later. Terminal failures are retained, not retried.
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
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    lock_path = ROOT / f"logs/koios-prepare-seed{args.seed}.lock"
    lock = lock_path.open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    lock.write(str(os.getpid()))
    lock.flush()
    records = json.loads((ROOT / "benchmarks/beyond_flatland.lock.json").read_text())["files"]
    queue = []
    for item in records:
        path = ROOT / item["files"][0]["path"]
        name = path.stem
        # Reuse the already validated first preparation, without resubmission.
        output_name = "koios_conv_hls_seed1_v3" if name == "conv_layer_hls" and args.seed == 1 else f"koios_{name}_seed{args.seed}"
        queue.append({"circuit": name, "input": str(path), "output": str(ROOT / "results/runs" / output_name), "state": "queued"})
    state = {"owner_pid": os.getpid(), "goal_thread": "01a16354-a951-71f2-9de3-bbe121098a67",
             "workers": args.workers, "seed": args.seed, "started_epoch": time.time(),
             "monitoring": "same-session deterministic queue; no supported luna handoff", "jobs": queue}
    state_path = ROOT / f"results/koios_prepare_seed{args.seed}.json"

    def save():
        temp = state_path.with_suffix(".tmp")
        temp.write_text(json.dumps(state, indent=2) + "\n")
        temp.replace(state_path)

    def prepare(job):
        output = Path(job["output"])
        manifest = output / "manifest.json"
        if manifest.exists():
            prior = json.loads(manifest.read_text())
            if prior["status"] == "running":
                raise RuntimeError(f"Existing live/interrupted run requires inspection before recovery: {output}")
            return prior
        command = [sys.executable, str(ROOT / "scripts/run_vpr.py"),
                   "--arch", str(ROOT / "configs/architectures/koios_native3d_n6_f16_d1_v3.xml"),
                   "--circuit", job["input"], "--device-width", "0", "--utilization", "0.6", "--width", "100",
                   "--seed", str(args.seed), "--timeout", str(args.timeout), "--output", str(output)]
        with (ROOT / f"logs/prepare_{job['circuit']}_seed{args.seed}.log").open("w") as stream:
            subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=False)
        return json.loads(manifest.read_text())

    save()
    # Submit at most workers jobs at once, making queue state reflect execution.
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        pending = {}
        cursor = 0
        while cursor < len(queue) or pending:
            while cursor < len(queue) and len(pending) < args.workers:
                job = queue[cursor]
                cursor += 1
                job["state"] = "running"
                pending[pool.submit(prepare, job)] = job
                save()
            done, _ = concurrent.futures.wait(pending, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                job = pending.pop(future)
                try:
                    result = future.result()
                    job.update(state=result["status"], metrics=result.get("metrics", {}),
                               process_wall_seconds=result.get("process_wall_seconds"))
                except Exception as error:
                    job.update(state="supervisor_error", error=str(error))
                save()
                print(json.dumps(job), flush=True)
    state["finished_epoch"] = time.time()
    save()


if __name__ == "__main__":
    main()
