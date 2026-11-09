#!/usr/bin/env python3
"""Three sequential paired timing repeats, with deterministic shuffled order.

Run only after the experiment/audit queues finish. This removes contention from
our own VPR jobs; it does not claim exclusive access to the shared host.
"""
import fcntl
import json
import os
from pathlib import Path
import random
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]


def main():
    lock = (ROOT / "logs/controlled_timing.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    lock.write(str(os.getpid()))
    lock.flush()
    # Earlier independent audits may overlap the screening queues. Wait for
    # those exact owned processes as well; PID start times prevent reuse errors.
    preaudits = ROOT / "logs/preaudit_processes.json"
    if preaudits.exists():
        for record in json.loads(preaudits.read_text()):
            while True:
                stat = Path(f"/proc/{record['pid']}/stat")
                try:
                    fields = stat.read_text().split()
                except FileNotFoundError:
                    break
                if fields[21] != record["start_ticks"] or fields[2] == "Z":
                    break
                time.sleep(10)
    variants = json.loads((ROOT / "configs/variants_all.json").read_text()) + json.loads((ROOT / "configs/variants_prune_controls.json").read_text())
    variants.append({"name": "a0_instrumented", "binary": "artifacts/bin/controls/vpr", "env": {"VPR_H3D_STATS": "1"}})
    # The selected A1 weight equals the early A1 setting, but its newer archived
    # binary includes dormant planner/control branches; measure both versions.
    variants.extend(json.loads((ROOT / "configs/variants_tuned.json").read_text()))
    cases = {"ex5p_balanced": ROOT / "results/runs/fixture_ex5p_balanced1", "conv_layer_hls": ROOT / "results/runs/koios_conv_hls_seed1_v3"}
    rng = random.Random(20261022)
    jobs = []
    for case, prepared in cases.items():
        for repeat in [1, 2, 3]:
            order = list(variants)
            rng.shuffle(order)
            for variant in order:
                jobs.append({"circuit": case, "prepared": str(prepared), "repeat": repeat, "variant": variant["name"],
                             "settings": variant, "state": "queued", "output": str(ROOT / f"results/runs/timing_{case}_r{repeat}_{variant['name']}")})
    state = {"owner_pid": os.getpid(), "started_epoch": time.time(), "workers": 1,
             "scope": "Sequential after our own matrices/audits finish; shared host, not CPU-frequency isolation", "jobs": jobs}
    path = ROOT / "results/controlled_timing.json"

    def save():
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(state, indent=2) + "\n")
        temp.replace(path)

    save()
    for job in jobs:
        output = Path(job["output"])
        manifest = output / "manifest.json"
        if manifest.exists():
            result = json.loads(manifest.read_text())
            if result["status"] == "running":
                raise RuntimeError("Live/interrupted timing run requires inspection")
        else:
            job["state"] = "running"
            save()
            variant = job["settings"]
            command = ["python3", str(ROOT / "scripts/run_vpr.py"), "--reuse", job["prepared"], "--output", job["output"],
                       "--binary", str(ROOT / variant["binary"])]
            for key, value in variant.get("env", {}).items():
                command.extend(["--env", key + "=" + value])
            command.extend(["--extra", "--generate_net_timing_report", "on", *variant.get("extra", [])])
            with (ROOT / f"logs/{output.name}.log").open("w") as stream:
                subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=False)
            result = json.loads(manifest.read_text())
        job.update(state=result["status"], metrics=result["metrics"], process_wall_seconds=result["process_wall_seconds"], peak_rss_kib=result["peak_rss_kib"])
        save()
        print(json.dumps({key: job[key] for key in ("circuit", "variant", "repeat", "state", "metrics")}), flush=True)
    state["finished_epoch"] = time.time()
    save()


if __name__ == "__main__":
    main()
