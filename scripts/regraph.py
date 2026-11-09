#!/usr/bin/env python3
"""Generate a changed native RRG while holding the packed netlist and placement fixed.

Only scatter/gather access, its segment and named switch may change. This
rejects hidden layout, primitive, pin or planar routing changes. The resulting
preparation is reusable by run_vpr.py for paired router comparisons.
"""
import argparse
import copy
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import xml.etree.ElementTree as ET

from check_route import sha256
from run_vpr import parse_metrics

ROOT = Path(__file__).resolve().parents[1]


def invariant(path):
    root = ET.parse(path).getroot()
    scatter = root.find("scatter_gather_list")
    if scatter is None:
        raise ValueError("Architecture is not native scatter/gather")
    z_switches = {link.get("mux") for link in scatter.findall("sg_pattern/sg_link_list/sg_link")}
    root.remove(scatter)
    z_segments = [s for s in root.find("segmentlist") if s.get("axis") == "z" or s.get("name") == "z_segment"]
    for segment in z_segments:
        z_switches.add(segment.find("mux").get("name"))
        root.find("segmentlist").remove(segment)
    for switch in list(root.find("switchlist")):
        if switch.get("name") in z_switches:
            root.find("switchlist").remove(switch)
    # Ignore serialization whitespace while preserving attributes and order.
    for element in root.iter():
        element.text = (element.text or "").strip()
        element.tail = ""
    return ET.tostring(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--arch", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--width", type=int, help="Explicit separate channel-width experiment; keep placement fixed")
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    prior = json.loads((source / "manifest.json").read_text())
    width = args.width if args.width is not None else prior["route_chan_width"]
    if width < 1:
        parser.error("width must be positive")
    old_arch = Path(prior["inputs"]["architecture"]["path"])
    if invariant(old_arch) != invariant(args.arch):
        raise ValueError("Architecture changes exceed the allowed native-Z sweep")
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("Refusing to overwrite an experiment")
    for filename in ("packed.net", "fixed.place"):
        if sha256(source / filename) != prior["outputs"][filename]["sha256"]:
            raise ValueError("Frozen placement/netlist changed")
        (output / filename).symlink_to(source / filename)
    command = [str(ROOT / "artifacts/bin/baseline/vpr"), str(args.arch.resolve()), prior["inputs"]["circuit"]["path"],
               "--route_chan_width", str(width), "--device_width", str(prior["device_width"]),
               "--target_utilization", str(prior.get("target_utilization", .1)), "--seed", str(prior["seed"]),
               "--num_workers", "1", "--router_algorithm", "timing_driven", "--flat_routing", "off",
               "--check_route", "full", "--timing_report_npaths", "10", "--verify_file_digests", "off"]
    for flag, filename in (("--net_file", "packed.net"), ("--place_file", "fixed.place"), ("--route_file", "routed.route")):
        command.extend([flag, str(output / filename)])
    command.extend(["--route", "--analysis", "--write_rr_graph", str(output / "rr_graph.xml")])
    manifest = {key: copy.deepcopy(prior[key]) for key in ("route_chan_width", "device_width", "seed")}
    manifest["target_utilization"] = prior.get("target_utilization", .1)
    manifest["route_chan_width"] = width
    inputs = {"binary": Path(command[0]), "architecture": args.arch.resolve(),
              "circuit": Path(prior["inputs"]["circuit"]["path"]), "packed_netlist": source / "packed.net", "placement": source / "fixed.place"}
    manifest.update(schema=1, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), command=command, cwd=str(output),
                    inputs={k: {"path": str(v), "sha256": sha256(v)} for k, v in inputs.items()},
                    architecture_sweep_source=str(source), experimental_environment={}, status="running")
    manifest["compatible_architecture_change"] = {"original_architecture": str(old_arch),
                                                  "original_architecture_sha256": sha256(old_arch),
                                                  "exception": "Disable native packed architecture digest check only after exact equality of all non-Z architecture sections; wrapper verifies frozen bytes"}
    env = {k: v for k, v in os.environ.items() if not k.startswith("VPR_H3D_")}
    manifest_path = output / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    start = time.monotonic()
    with (output / "vpr.log").open("w") as stream:
        process = subprocess.Popen(["/usr/bin/time", "-v", "-o", str(output / "resource_usage.txt"), *command],
                                   cwd=output, env=env, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        manifest.update(supervisor_pid=os.getpid(), process_group_id=process.pid)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        try:
            code = process.wait(timeout=args.timeout)
            manifest.update(status="completed" if code == 0 else "failed", returncode=code)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            manifest.update(status="timeout", returncode=process.returncode)
    manifest.update(process_wall_seconds=time.monotonic() - start,
                    metrics=parse_metrics((output / "vpr.log").read_text(errors="replace")))
    manifest["outputs"] = {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in output.iterdir() if p.is_file() and p != manifest_path}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"status": manifest["status"], "metrics": manifest["metrics"]}))


if __name__ == "__main__":
    main()
