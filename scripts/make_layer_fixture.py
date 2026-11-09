#!/usr/bin/env python3
"""Create a labeled two-die fixed-placement fixture from a prepared small run.

Only CLB clusters move, at identical XY/subtile sites whose exact RRG grid tile
types/offsets match across dies. This is a synthetic stress fixture, not a result
of a 3D placement optimizer. VPR must still validate the derived placement.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from check_route import sha256


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=1)
    args = parser.parse_args()
    source = args.source.resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        parser.error("output must be empty")
    original = json.loads((source / "manifest.json").read_text())
    grid = {}
    with (source / "rr_graph.xml").open("rb") as stream:
        for event, element in ET.iterparse(stream, events=("start", "end")):
            if event == "start" and element.tag == "rr_nodes":
                break
            if event == "end" and element.tag == "grid_loc":
                a = element.attrib
                grid[(int(a["x"]), int(a["y"]), int(a["layer"]))] = (
                    a["block_type_id"], a["width_offset"], a["height_offset"])
    root = ET.parse(source / "packed.net").getroot()
    clbs = {block.attrib["name"] for block in root.findall("block") if block.attrib["instance"].startswith("clb[")}
    lines = (source / "fixed.place").read_text().splitlines()
    records = []
    occupied = set()
    for index, line in enumerate(lines):
        if not line.strip() or line.startswith(("#", "Netlist", "Array")):
            continue
        fields = line.split()
        x, y, subtile, layer = map(int, fields[1:5])
        records.append((index, fields, x, y, subtile, layer))
        occupied.add((x, y, subtile, layer))
    before = Counter(record[5] for record in records if record[1][0] in clbs)
    if len(before) != 1:
        raise ValueError("This fixture generator expects all CLB clusters initially on one die")
    candidates = []
    for record in records:
        index, fields, x, y, subtile, layer = record
        target = 1 - layer
        if fields[0] not in clbs or (x, y, subtile, target) in occupied:
            continue
        if grid.get((x, y, layer)) != grid.get((x, y, target)):
            continue
        key = hashlib.sha256(f"{args.seed}:{fields[0]}".encode()).digest()
        candidates.append((key, record))
    candidates.sort(key=lambda item: item[0])
    moved = []
    for _, (index, fields, x, y, subtile, layer) in candidates[:len(clbs) // 2]:
        fields[4] = str(1 - layer)
        lines[index] = "\t".join(fields)
        moved.append(fields[0])
    if len(moved) != len(clbs) // 2:
        raise ValueError("Not enough compatible free sites to construct a balanced CLB fixture")
    (output / "fixed.place").write_text("\n".join(lines) + "\n")
    for name in ("packed.net", "rr_graph.xml"):
        (output / name).symlink_to(source / name)
    manifest = {key: original[key] for key in ("schema", "inputs", "route_chan_width", "device_width", "seed")}
    manifest.update(status="constructed_placement_fixture_requires_vpr_validation",
                    fixture={"kind": "balanced_clb_random_layer_partition", "seed": args.seed,
                             "source_manifest": str(source / "manifest.json"),
                             "source_placement_sha256": sha256(source / "fixed.place"),
                             "moved_clusters": moved, "initial_clb_layers": dict(before),
                             "note": "Identical XY/subtile, matched native tile types/offsets; not optimized 3D placement."},
                    outputs={name: {"sha256": sha256(output / name), "bytes": (output / name).stat().st_size}
                             for name in ("packed.net", "fixed.place", "rr_graph.xml")})
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"clb_clusters": len(clbs), "moved": len(moved), "output": str(output)}))


if __name__ == "__main__":
    main()
