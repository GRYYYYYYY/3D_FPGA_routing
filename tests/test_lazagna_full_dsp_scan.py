"""Full DSP endpoint scanning must compare physical identities, not IDs."""
import sys
import tempfile
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from audit_lazagna_dsp_correspondence import scan


def fixture(pin,node,layer_format='old',capacity=1,connected=True):
    layer='layer="1"' if layer_format=='old' else 'layer_low="1" layer_high="1"'
    edge=f'<edge src_node="{pin}" sink_node="{node}" switch_id="3"/>' if connected else ''
    return f'''<rr_graph><segments><segment id="0" name="L4"/></segments>
    <block_types><block_type id="1" name="complex_dsp"/></block_types>
    <grid><grid_loc x="2" y="3" layer="1" block_type_id="1"/></grid>
    <rr_nodes><node id="{node}" type="CHANY" direction="INC_DIR" capacity="{capacity}">
    <loc xlow="1" xhigh="1" ylow="1" yhigh="4" ptc="8" {layer}/><segment segment_id="0"/></node>
    <node id="{pin}" type="OPIN" capacity="1"><loc xlow="2" xhigh="2" ylow="3" yhigh="3" ptc="74" side="LEFT" {layer}/></node>
    </rr_nodes><rr_edges>{edge}</rr_edges></rr_graph>'''


class FullDspScan(unittest.TestCase):
    def test_renumbered_nodes_and_layer_serialization_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b=(Path(tmp)/x for x in ('a.xml','b.xml'))
            a.write_text(fixture(99,5));b.write_text(fixture(1,400,'new'))
            self.assertEqual(scan(a)[0],scan(b)[0])

    def test_missing_exit_or_different_capacity_is_not_equivalent(self):
        with tempfile.TemporaryDirectory() as tmp:
            a,b=(Path(tmp)/x for x in ('a.xml','b.xml'))
            a.write_text(fixture(99,5));reference=scan(a)[0]
            b.write_text(fixture(1,400,capacity=2));self.assertNotEqual(reference,scan(b)[0])
            b.write_text(fixture(1,400,connected=False));self.assertNotEqual(reference,scan(b)[0])


if __name__=='__main__':unittest.main()
