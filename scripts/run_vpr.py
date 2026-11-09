#!/usr/bin/env python3
"""Run an isolated fixed-width VPR experiment with immutable input hashes.

Prepare packs/places/routes a circuit and exports XML RRG. Route-only runs reuse
that exact packed netlist, placement and graph; no placement is regenerated.
Failed and timed-out runs retain commands, logs and output hashes.
"""

import argparse
import datetime
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

from check_route import sha256

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARCH = ROOT / "vendor/vtr/vtr_flow/arch/multi_die/hecate/3d/hecate_3d_sb_10um_bidir_fanin_16_fanout_16_with_esd_7nm.xml"


def parse_metrics(log):
    """Extract native reported values without treating failure as a solution."""
    result = {}
    patterns = {
        "critical_path_ns": r"Final critical path delay \(least slack\):\s+([\d.eE+-]+)\s+ns",
        "wirelength": r"Total wirelength:\s+(\d+)",
        "router_seconds": r"Routing took\s+([\d.eE+-]+)\s+seconds",
        "iterations": r"Successfully routed after\s+(\d+)\s+routing iterations",
    }
    for key, pattern in patterns.items():
        matches = re.findall(pattern, log)
        if matches:
            result[key] = float(matches[-1]) if key not in ("wirelength", "iterations") else int(matches[-1])
    result["native_full_check_passed"] = "Completed routing consistency check successfully." in log
    result["routing_success_reported"] = "Circuit successfully routed" in log
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, default=ROOT / "artifacts/bin/baseline/vpr")
    parser.add_argument("--arch", type=Path, default=DEFAULT_ARCH)
    parser.add_argument("--circuit", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reuse", type=Path, help="Prepared run directory for paired route-only experiment")
    parser.add_argument("--width", type=int, default=66)
    parser.add_argument("--device-width", type=int, default=30)
    parser.add_argument("--utilization", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--env", action="append", default=[], help="Explicit experimental setting NAME=VALUE")
    parser.add_argument("--extra", nargs=argparse.REMAINDER, default=[])
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        parser.error("output directory must be empty; preserve prior runs")
    binary = args.binary.resolve()
    arch = args.arch.resolve()
    reuse = args.reuse.resolve() if args.reuse else None
    if reuse:
        original = json.loads((reuse / "manifest.json").read_text())
        circuit = Path(original["inputs"]["circuit"]["path"])
        arch = Path(original["inputs"]["architecture"]["path"])
        args.width = original["route_chan_width"]
        args.device_width = original["device_width"]
        args.seed = original["seed"]
        args.utilization = original.get("target_utilization", 0.1)
    elif args.circuit:
        circuit = args.circuit.resolve()
    else:
        parser.error("--circuit is required when preparing a run")
    inputs = {"binary": binary, "architecture": arch, "circuit": circuit}
    command = [str(binary), str(arch), str(circuit),
               "--route_chan_width", str(args.width), "--device_width", str(args.device_width),
               "--target_utilization", str(args.utilization), "--seed", str(args.seed), "--num_workers", "1",
               "--router_algorithm", "timing_driven", "--flat_routing", "off", "--check_route", "full",
               "--net_file", str(output / "packed.net"), "--place_file", str(output / "fixed.place"),
               "--route_file", str(output / "routed.route"), "--timing_report_npaths", "10"]
    if reuse:
        for role, filename, option in [("packed_netlist", "packed.net", "--net_file"),
                                       ("placement", "fixed.place", "--place_file")]:
            source = reuse / filename
            command[command.index(option) + 1] = str(source)
            inputs[role] = source
        inputs["rr_graph"] = reuse / "rr_graph.xml"
        command.extend(["--route", "--analysis", "--read_rr_graph", str(inputs["rr_graph"])])
        if original.get("compatible_architecture_change"):
            from regraph import invariant
            exception = original["compatible_architecture_change"]
            old_arch = Path(exception["original_architecture"])
            if sha256(old_arch) != exception["original_architecture_sha256"] or invariant(old_arch) != invariant(arch):
                raise RuntimeError("Architecture compatibility proof no longer holds")
            command.extend(["--verify_file_digests", "off"])
        # Ensure even unchanged paths still contain the prepared bytes.
        for role in ("architecture", "circuit"):
            if sha256(inputs[role]) != original["inputs"][role]["sha256"]:
                raise RuntimeError(f"Prepared {role} changed on disk")
        for role, filename in (("packed_netlist", "packed.net"), ("placement", "fixed.place"), ("rr_graph", "rr_graph.xml")):
            if sha256(inputs[role]) != original["outputs"][filename]["sha256"]:
                raise RuntimeError(f"Prepared {role} changed on disk")
    else:
        command.extend(["--pack", "--place", "--route", "--analysis", "--write_rr_graph", str(output / "rr_graph.xml")])
    command.extend(args.extra)
    env = os.environ.copy()
    # Do not inherit experimental flags silently from the terminal.
    for key in list(env):
        if key.startswith("VPR_H3D_"):
            del env[key]
    overrides = {}
    for entry in args.env:
        key, value = entry.split("=", 1)
        if not key.startswith("VPR_H3D_"):
            parser.error("experimental environment keys must start with VPR_H3D_")
        overrides[key] = value
    env.update(overrides)
    if overrides.get("VPR_H3D_CONTROL", "off") != "off":
        lut = Path(overrides["VPR_H3D_FLUTE_LUT"])
        inputs["flute_powv_lut"] = lut / "POWV9.dat"
        inputs["flute_post_lut"] = lut / "POST9.dat"
    manifest = {"schema": 1, "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "command": command, "cwd": str(output), "experimental_environment": overrides,
                "inputs": {key: {"path": str(value), "sha256": sha256(value)} for key, value in inputs.items()},
                "reuse": str(reuse) if reuse else None, "route_chan_width": args.width,
                "device_width": args.device_width, "seed": args.seed, "timeout_seconds": args.timeout,
                "target_utilization": args.utilization,
                "status": "running"}
    if reuse and original.get("compatible_architecture_change"):
        manifest["compatible_architecture_change"] = original["compatible_architecture_change"]
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    timed_command = ["/usr/bin/time", "-v", "-o", str(output / "resource_usage.txt"), *command]
    started = time.monotonic()
    with (output / "vpr.log").open("w") as stream:
        process = subprocess.Popen(timed_command, cwd=output, stdout=stream, stderr=subprocess.STDOUT,
                                   env=env, start_new_session=True)
        manifest.update(supervisor_pid=os.getpid(), process_group_id=process.pid)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        try:
            returncode = process.wait(timeout=args.timeout)
            manifest.update(status="completed" if returncode == 0 else "failed", returncode=returncode)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            manifest.update(status="timeout", returncode=process.returncode)
    manifest["process_wall_seconds"] = time.monotonic() - started
    manifest["metrics"] = parse_metrics((output / "vpr.log").read_text(errors="replace"))
    usage = (output / "resource_usage.txt").read_text() if (output / "resource_usage.txt").exists() else ""
    peak = re.search(r"Maximum resident set size \(kbytes\):\s+(\d+)", usage)
    manifest["peak_rss_kib"] = int(peak[1]) if peak else None
    manifest["outputs"] = {path.name: {"bytes": path.stat().st_size, "sha256": sha256(path)}
                           for path in output.iterdir() if path.is_file() and path != manifest_path}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({key: manifest[key] for key in ("status", "process_wall_seconds", "peak_rss_kib", "metrics")}, indent=2))
    return 0 if manifest["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
