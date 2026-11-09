#!/usr/bin/env python3
"""Prepare five MCNC circuits at three paired placement/partition seeds.

Single-layer CLB placements are converted to explicitly labeled balanced stress
fixtures. Already mixed placements are retained and labeled as natural. The
original pack/place/route run, including any failure, is always preserved.
"""
import concurrent.futures
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def main():
    lock = (ROOT / "logs/paired_seed_prepare.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    lock.write(str(os.getpid()))
    lock.flush()
    jobs = [{"circuit": f"{c}_seed{s}", "benchmark": c, "seed": s, "state": "queued",
             "output": str(ROOT / f"results/runs/fixture_{c}_balanced{s}")}
            for c in ["alu4", "ex5p", "diffeq", "elliptic", "tseng"] for s in [1, 2, 3]]
    state = {"owner_pid": os.getpid(), "started_epoch": time.time(), "jobs": jobs}
    path = ROOT / "results/paired_seed_prepare.json"

    def save():
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(state, indent=2) + "\n")
        temp.replace(path)

    def prepare(job):
        c, seed = job["benchmark"], job["seed"]
        original = ROOT / f"results/runs/baseline_{c}_w100_seed{seed}"
        manifest = original / "manifest.json"
        log = ROOT / f"logs/paired_prepare_{c}_seed{seed}.log"
        if not manifest.exists():
            with log.open("w") as stream:
                subprocess.run(["python3", str(ROOT / "scripts/run_vpr.py"), "--circuit",
                                str(ROOT / f"vendor/vtr/vtr_flow/benchmarks/blif/{c}.blif"), "--width", "100",
                                "--seed", str(seed), "--output", str(original)], stdout=stream, stderr=subprocess.STDOUT, check=False)
        prior = json.loads(manifest.read_text())
        if prior["status"] == "running":
            raise RuntimeError("Live/interrupted preparation needs inspection")
        if not all(n in prior.get("outputs", {}) for n in ["packed.net", "fixed.place", "rr_graph.xml"]):
            return {"state": "unavailable_inputs", "output": str(original), "preparation_status": prior["status"]}
        clbs = {b.get("name") for b in ET.parse(original / "packed.net").getroot().findall("block") if b.get("instance", "").startswith("clb[")}
        layers = set()
        for line in (original / "fixed.place").read_text().splitlines():
            fields = line.split()
            if fields and fields[0] in clbs:
                layers.add(int(fields[4]))
        if len(layers) > 1:
            return {"state": "completed", "output": str(original), "placement_kind": "natural_mixed", "preparation_status": prior["status"]}
        fixture = Path(job["output"])
        if not (fixture / "manifest.json").exists():
            with log.open("a") as stream:
                subprocess.run(["python3", str(ROOT / "scripts/make_layer_fixture.py"), "--source", str(original),
                                "--output", str(fixture), "--seed", str(seed)], stdout=stream, stderr=subprocess.STDOUT, check=True)
        return {"state": "completed", "placement_kind": "balanced_clb_stress", "preparation_status": prior["status"]}

    save()
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        pending = {}
        cursor = 0
        while cursor < len(jobs) or pending:
            while cursor < len(jobs) and len(pending) < 2:
                job = jobs[cursor]
                cursor += 1
                job["state"] = "running"
                pending[pool.submit(prepare, job)] = job
                save()
            done, _ = concurrent.futures.wait(pending, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                job = pending.pop(future)
                try:
                    job.update(future.result())
                except Exception as error:
                    job.update(state="supervisor_error", error=str(error))
                save()
                print(json.dumps(job), flush=True)
    state["finished_epoch"] = time.time()
    save()


if __name__ == "__main__":
    main()
