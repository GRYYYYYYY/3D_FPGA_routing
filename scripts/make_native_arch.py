#!/usr/bin/env python3
"""Adapt the published Koios hard-block architecture to explicit native CHANZ.

Preserve source primitives, local timing and planar switchblocks. Replace its
legacy inter-layer encoding with the pinned VTR Hecate scatter/gather model.
This is a documented hybrid research architecture, not the original paper's
fabric or a claim of process-calibrated physical equivalence.
"""

import argparse
import copy
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from check_route import sha256

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "benchmarks/downloads/beyond_flatland/sb_architecture.xml"
NATIVE = ROOT / "vendor/vtr/vtr_flow/arch/multi_die/hecate/3d/hecate_3d_sb_10um_bidir_fanin_16_fanout_16_with_esd_7nm.xml"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--channels", type=int, default=6)
    parser.add_argument("--fanin", type=int, default=16)
    parser.add_argument("--fanout", type=int, default=16)
    parser.add_argument("--delay-scale", type=float, default=1.)
    parser.add_argument("--location", choices=("EVERYWHERE", "CORE", "PERIMETER"), default="EVERYWHERE")
    args = parser.parse_args()
    if min(args.channels, args.fanin, args.fanout, args.delay_scale) <= 0:
        parser.error("channel/access counts and delay scale must be positive")
    root = ET.parse(SOURCE).getroot()
    native = ET.parse(NATIVE).getroot()
    # A flexible auto layout uses the exact two source layer definitions.
    layout = root.find("layout")
    layers = [copy.deepcopy(item) for item in layout[0].findall("layer")]
    layout.clear()
    automatic = ET.SubElement(layout, "auto_layout", {"aspect_ratio": "1.0"})
    automatic.extend(layers)
    segmentlist = root.find("segmentlist")
    for segment in list(segmentlist):
        if segment.get("name") == "3D_SB_connection":
            segmentlist.remove(segment)
        else:
            for item in list(segment):
                if item.tag == "mux_inter_die":
                    segment.remove(item)
    native_z = next(item for item in native.find("segmentlist") if item.get("name") == "z_segment")
    native_z = copy.deepcopy(native_z)
    native_z.find("mux").set("name", "bidir_inter_die_switch_10um_with_esd")
    segmentlist.append(native_z)
    sb_list = root.find("switchblocklist")
    removed = []
    for item in list(sb_list):
        if item.get("name") == "3d_subset":
            removed.append(item.get("name"))
            sb_list.remove(item)
    assert removed == ["3d_subset"]
    switches = root.find("switchlist")
    for item in list(switches):
        if "inter_layer" in item.get("name", "") or item.get("name") == "3D_SB_switch":
            switches.remove(item)
    crossing_name = "bidir_inter_die_switch_10um_with_esd"
    crossing = copy.deepcopy(next(item for item in native.find("switchlist") if item.get("name") == crossing_name))
    for delay in crossing.findall("Tdel"):
        delay.set("delay", f"{float(delay.get('delay')) * args.delay_scale:.12g}")
    switches.append(crossing)
    connection_block = root.find("device/connection_block")
    connection_block.attrib.pop("input_inter_die_switch_name", None)
    # The SB experiment has no direct pin-to-Z connection. Without this
    # override a generic fractional Fc also applies to the new Z segment.
    for fc in root.findall("tiles/tile/sub_tile/fc"):
        ET.SubElement(fc, "fc_override", {"fc_type": "abs", "fc_val": "0", "segment_name": "z_segment"})
    scatter = copy.deepcopy(native.find("scatter_gather_list"))
    pattern = scatter.find("sg_pattern")
    pattern.set("name", "native_koios_bidir")
    for location in list(pattern.findall("sg_location")):
        pattern.remove(location)
    ET.SubElement(pattern, "sg_location", {"type": args.location, "num": str(args.channels), "sg_link_name": "L_UP"})
    pattern.find("gather/wireconn").set("num_conns", str(args.fanin))
    pattern.find("scatter/wireconn").set("num_conns", str(args.fanout))
    root.append(scatter)
    ET.indent(root, space="  ")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        raise RuntimeError("Refusing to overwrite an existing experiment architecture")
    ET.ElementTree(root).write(args.output, encoding="utf-8", xml_declaration=True)
    provenance = {"schema": 1, "description": __doc__,
                  "source_architecture": {"path": str(SOURCE), "sha256": sha256(SOURCE),
                                          "commit": "84ba44acf1bad597bc5a9d1f615415870e178a86"},
                  "native_vertical_model": {"path": str(NATIVE), "sha256": sha256(NATIVE)},
                  "output_sha256": sha256(args.output),
                  "parameters": {key: value for key, value in vars(args).items() if key != "output"},
                  "preserved_sections": ["models", "complexblocklist", "planar switchblocks"],
                  "tile_change": "Preserve local pins/capacities; add Fc=0 override for direct pin-to-CHANZ edges",
                  "limitations": ["mixed-source timing model; no process-equivalence claim", "zero wire RC in source models; fanout/load sensitivity limited", "new vertical topology, not reproduction of original Beyond-Flatland routing"]}
    args.output.with_suffix(".provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "sha256": provenance["output_sha256"]}))


if __name__ == "__main__":
    main()
