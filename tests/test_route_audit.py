"""Failure-injection checks for independent graph/trace auditing."""

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

MODULE = Path(__file__).resolve().parents[1] / "scripts" / "check_route.py"
SPEC = importlib.util.spec_from_file_location("route_audit", MODULE)
AUDIT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AUDIT
SPEC.loader.exec_module(AUDIT)


class RouteAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.graph = self.root / "rr.xml"
        self.route = self.root / "test.route"
        self.nodes = [(0, "SOURCE", 0, 0, 1), (1, "CHANX", 0, 0, 1),
                      (2, "CHANZ", 0, 1, 1), (3, "SINK", 1, 1, 2),
                      (4, "CHANY", 1, 1, 1)]
        self.edges = [(0, 1, 0), (1, 2, 0), (2, 3, 0), (2, 4, 0), (4, 3, 0)]
        self.trace = [(0, 0, None), (1, 0, None), (2, 0, None), (3, -1, 1),
                      (2, 0, None), (4, 0, None), (3, -1, 2)]

    def run_audit(self, second_net=False, resource_map=None):
        xml = ['<rr_graph><rr_nodes>']
        for inode, kind, zl, zh, capacity in self.nodes:
            xml.append(f'<node id="{inode}" type="{kind}" capacity="{capacity}" direction="BI_DIR">'
                       f'<loc xlow="0" xhigh="0" ylow="0" yhigh="0" layer_low="{zl}" layer_high="{zh}" ptc="0"/>'
                       '<timing R="0" C="0"/></node>')
        xml.append('</rr_nodes><rr_edges>')
        xml.extend(f'<edge src_node="{a}" sink_node="{b}" switch_id="{c}"/>' for a, b, c in self.edges)
        xml.append('</rr_edges></rr_graph>')
        self.graph.write_text("\n".join(xml))
        by_id = {node[0]: node for node in self.nodes}
        lines = []
        for net_id in range(2 if second_net else 1):
            lines.append(f"Net {net_id} (test{net_id})")
            for inode, switch, pin in self.trace:
                _, kind, zl, zh, _ = by_id[inode]
                location = f"(0,0,{zl})" + (f" to (0,0,{zh})" if zl != zh else "")
                lines.append(f"Node: {inode} {kind} {location} Track: 0 Switch: {switch}"
                             + (f" Net_pin_index: {pin}" if pin is not None else ""))
        self.route.write_text("\n".join(lines))
        return AUDIT.audit(self.graph, self.route, resource_map)

    def test_shared_crossing_and_repeated_sink_class(self):
        result = self.run_audit()
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["route"]["vertical_channel_net_occupancy"], 1)
        self.assertEqual(result["route"]["sink_terminals"], 2)
        self.assertEqual(result["route"]["cross_layer_sink_connections"], 2)

    def test_same_sink_class_still_consumes_two_capacity(self):
        self.nodes[3] = (3, "SINK", 1, 1, 1)
        result = self.run_audit()
        self.assertFalse(result["passed"])
        self.assertEqual(result["route"]["overused_rr_nodes"], 1)

    def test_reversed_edge_is_not_connectivity(self):
        self.edges[1] = (2, 1, 0)
        result = self.run_audit()
        self.assertTrue(any("missing directed edge" in error for error in result["errors"]))

    def test_wrong_switch_rejected(self):
        self.edges[1] = (1, 2, 4)
        self.assertFalse(self.run_audit()["passed"])

    def test_detached_branch_rejected(self):
        self.trace[4] = (4, 0, None)
        result = self.run_audit()
        self.assertTrue(any("detached" in error for error in result["errors"]))

    def test_two_nets_cannot_share_bidir_vertical_channel(self):
        result = self.run_audit(second_net=True)
        self.assertFalse(result["passed"])
        self.assertEqual(result["route"]["vertical_channel_net_occupancy"], 2)
        self.assertEqual(result["route"]["unique_used_vertical_channels"], 1)

    def test_native_chanz_span_reports_layer_hops(self):
        self.nodes[2] = (2, "CHANZ", 0, 3, 1)
        self.assertEqual(self.run_audit()["nets"]["0"]["native_layer_hops"], 3)

    def test_duplicate_terminal_index_rejected(self):
        self.trace[-1] = (3, -1, 1)
        self.assertFalse(self.run_audit()["passed"])

    def test_legacy_pair_counted_once_only_with_explicit_mapping(self):
        self.nodes[1] = (1, "CHANX", 0, 0, 1)
        self.nodes[2] = (2, "CHANX", 1, 1, 1)
        mapping = self.root / "physical.json"
        mapping.write_text(json.dumps({"channels": {"legacy:0": {"nodes": [1, 2], "capacity": 1}}}))
        result = self.run_audit(resource_map=mapping)
        self.assertTrue(result["passed"], result["errors"])
        self.assertEqual(result["route"]["vertical_channel_net_occupancy"], 1)
        self.assertEqual(self.run_audit()["route"]["vertical_channel_net_occupancy"], 0)

    def test_zero_rc_delays_follow_branch_restarts_and_sink_instances(self):
        self.run_audit()
        tree = ET.parse(self.graph)
        switches = ET.SubElement(tree.getroot(), "switches")
        switch = ET.SubElement(switches, "switch", id="0", type="mux")
        ET.SubElement(switch, "timing", Tdel="2e-10")
        tree.write(self.graph)
        evidence = AUDIT.batch_graph_evidence(self.graph, [self.route])
        result = AUDIT.audit(self.graph, self.route, graph_evidence=evidence)
        self.assertTrue(result["routed_connection_delays"]["available"])
        self.assertAlmostEqual(result["nets"]["0"]["routed_sink_delay_ns"]["1"], .6)
        self.assertAlmostEqual(result["nets"]["0"]["routed_sink_delay_ns"]["2"], .8)

    def test_nonzero_rc_does_not_use_fixed_delay_sum(self):
        self.run_audit()
        tree = ET.parse(self.graph)
        tree.find("rr_nodes/node/timing").set("R", "1")
        tree.write(self.graph)
        result = AUDIT.audit(self.graph, self.route)
        self.assertTrue(result["passed"])
        self.assertFalse(result["routed_connection_delays"]["available"])

    def test_unknown_legacy_resource_is_rejected(self):
        mapping = self.root / "physical.json"
        mapping.write_text(json.dumps({"channels": {"legacy:missing": {"nodes": [999], "capacity": 1}}}))
        with self.assertRaisesRegex(ValueError, "absent RRG"):
            self.run_audit(resource_map=mapping)


if __name__ == "__main__":
    unittest.main()
