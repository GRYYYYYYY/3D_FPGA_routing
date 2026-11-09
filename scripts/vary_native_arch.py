#!/usr/bin/env python3
"""Change only native vertical channel count, access, location or switch delay."""
import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET
from check_route import sha256


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--channels", type=int, default=6)
    p.add_argument("--fanin", type=int, default=16)
    p.add_argument("--fanout", type=int, default=16)
    p.add_argument("--delay-scale", type=float, default=1.)
    p.add_argument("--location", choices=["EVERYWHERE", "CORE", "PERIMETER"], default="EVERYWHERE")
    a = p.parse_args()
    if min(a.channels, a.fanin, a.fanout, a.delay_scale) <= 0:
        p.error("All counts and scales must be positive")
    if a.output.exists():
        p.error("Refusing to overwrite architecture")
    tree = ET.parse(a.source)
    root = tree.getroot()
    for pattern in root.findall("scatter_gather_list/sg_pattern"):
        link = pattern.find("sg_location").get("sg_link_name")
        for old in list(pattern.findall("sg_location")):
            pattern.remove(old)
        ET.SubElement(pattern, "sg_location", {"type": a.location, "num": str(a.channels), "sg_link_name": link})
        for wc in pattern.findall("gather/wireconn"):
            wc.set("num_conns", str(a.fanin))
        for wc in pattern.findall("scatter/wireconn"):
            wc.set("num_conns", str(a.fanout))
    # SG links select their actual edge switch independently of the Z segment
    # default mux; the bundled Hecate file uses different names for the two.
    switch_names = {link.get("mux") for link in root.findall("scatter_gather_list/sg_pattern/sg_link_list/sg_link")}
    for switch in root.find("switchlist"):
        if switch.get("name") not in switch_names:
            continue
        if switch.get("Tdel") is not None:
            switch.set("Tdel", str(float(switch.get("Tdel")) * a.delay_scale))
        for delay in switch.findall("Tdel"):
            delay.set("delay", f"{float(delay.get('delay')) * a.delay_scale:.12g}")
    ET.indent(root, space="  ")
    a.output.parent.mkdir(parents=True, exist_ok=True)
    tree.write(a.output, encoding="utf-8", xml_declaration=True)
    record = {"source": str(a.source.resolve()), "source_sha256": sha256(a.source), "output_sha256": sha256(a.output),
              "parameters": {k: v for k, v in vars(a).items() if k not in ("source", "output")},
              "scaled_switches": sorted(switch_names),
              "timing_scope": "parametric sensitivity of the supplied model; no newly calibrated process constants"}
    a.output.with_suffix(".provenance.json").write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    main()
