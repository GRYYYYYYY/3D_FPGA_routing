#!/usr/bin/env python3
"""Prepare 8 one-factor native-Z architectures on two fixed balanced placements."""
import concurrent.futures
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    lock = (ROOT / "logs/sweep_prepare_v4.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    lock.write(str(os.getpid()))
    lock.flush()
    cases = ["reference", "density3", "density12", "access8", "access32", "delay0p5", "delay2", "perimeter"]
    jobs = [{"circuit": f"{c}_{k}", "source": str(ROOT / f"results/runs/fixture_{c}_balanced1"),
             "arch": str(ROOT / f"configs/architectures/hecate_sweep_{k}.xml"),
             "output": str(ROOT / f"results/runs/sweep_prepare_{c}_{k}_v4"), "state": "queued"}
            for c in ["ex5p", "diffeq"] for k in cases]
    state = {"owner_pid": os.getpid(), "started_epoch": time.time(), "jobs": jobs}
    path = ROOT / "results/sweep_prepare_v4.json"

    def save():
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(state, indent=2) + "\n")
        temp.replace(path)

    def run(job):
        manifest = Path(job["output"]) / "manifest.json"
        if manifest.exists():
            prior = json.loads(manifest.read_text())
            if prior["status"] == "running":
                raise RuntimeError("Existing live/interrupted sweep requires inspection")
            return prior
        with (ROOT / f"logs/sweep_prepare_{job['circuit']}_v4.log").open("w") as stream:
            subprocess.run(["python3", str(ROOT / "scripts/regraph.py"), "--source", job["source"],
                            "--arch", job["arch"], "--output", job["output"]], stdout=stream, stderr=subprocess.STDOUT, check=False)
        return json.loads(manifest.read_text())

    save()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        pending = {}
        cursor = 0
        while cursor < len(jobs) or pending:
            while cursor < len(jobs) and len(pending) < 2:
                job = jobs[cursor]
                cursor += 1
                job["state"] = "running"
                pending[pool.submit(run, job)] = job
                save()
            done, _ = concurrent.futures.wait(pending, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                job = pending.pop(future)
                try:
                    result = future.result()
                    job.update(state=result["status"], metrics=result["metrics"])
                except Exception as error:
                    job.update(state="supervisor_error", error=str(error))
                save()
                print(json.dumps(job), flush=True)
    state["finished_epoch"] = time.time()
    save()


if __name__ == "__main__":
    main()
