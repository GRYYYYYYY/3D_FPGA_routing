#!/usr/bin/env python3
"""Single owner for terminal matrix audits followed by sequential timing checks.

This does not mark the research goal complete: final interpretation, review and
the reproducible report still require the main reasoning session.
"""
import fcntl
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
MATRICES = ["koios_a0a4_seed1", "koios_controls_seed1", "koios_prune_controls", "small_prune_controls",
            "natural_seeds_all", "tuned_heldout", "elliptic_w160_all"]
TERMINAL = {"completed", "failed", "timeout", "unavailable_inputs", "supervisor_error"}


def main():
    lock = (ROOT / "logs/final_validation_queue.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    lock.write(str(os.getpid()))
    lock.flush()
    path = ROOT / "results/final_validation_queue.json"
    state = {"owner_pid": os.getpid(), "started_epoch": time.time(), "stage": "waiting_matrices", "dependencies": MATRICES}

    def save():
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(state, indent=2) + "\n")
        temp.replace(path)

    save()
    previous = None
    while True:
        pending = {}
        for name in MATRICES:
            matrix = json.loads((ROOT / f"results/{name}.json").read_text())
            remaining = sum(j["state"] not in TERMINAL for j in matrix["jobs"])
            if remaining or "finished_epoch" not in matrix:
                pending[name] = remaining
        state["pending"] = pending
        save()
        if pending != previous:
            print(json.dumps({"waiting": pending}), flush=True)
            previous = pending
        if not pending:
            break
        time.sleep(30)

    stages = [
        ("audit_remaining", ["python3", str(ROOT / "scripts/audit_matrix.py"),
                             *[arg for name in MATRICES for arg in ("--matrix", str(ROOT / f"results/{name}.json"))],
                             "--output", str(ROOT / "results/audits_remaining.json"), "--workers", "2"]),
        ("sequential_timing", ["python3", str(ROOT / "scripts/run_timing_repeats.py")]),
        ("audit_timing", ["python3", str(ROOT / "scripts/audit_matrix.py"), "--matrix", str(ROOT / "results/controlled_timing.json"),
                          "--output", str(ROOT / "results/audits_timing.json"), "--workers", "2"]),
    ]
    for stage, command in stages:
        state.update(stage=stage, command=command)
        save()
        with (ROOT / f"logs/final_{stage}.log").open("w") as stream:
            process = subprocess.Popen(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT)
            state["child_pid"] = process.pid
            save()
            code = process.wait()
        state[stage + "_returncode"] = code
        save()
        if code:
            state["stage"] = "needs_failure_analysis"
            save()
            raise RuntimeError(f"Final validation stage failed: {stage}")
    state.update(stage="ready_for_final_analysis", finished_epoch=time.time())
    save()
    print(json.dumps(state), flush=True)


if __name__ == "__main__":
    main()
