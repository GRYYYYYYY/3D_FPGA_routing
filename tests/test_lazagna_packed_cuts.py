import sys
from pathlib import Path
import tempfile
import unittest
from lxml import etree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prove_lazagna_dsp_cuts import output_net,prove


class PackedCutTests(unittest.TestCase):
    def test_resolve_two_levels(self):
        b=ET.fromstring(b'''<block><outputs><port name="result">a[0].result[0]-&gt;m open</port></outputs>
          <block instance="a[0]"><outputs><port name="result">b[0].Y[0]-&gt;n</port></outputs>
          <block instance="b[0]"><outputs><port name="Y">external_net</port></outputs></block></block></block>''')
        self.assertEqual(output_net(b,'result',0),'external_net');self.assertIsNone(output_net(b,'result',1))

    def test_bad_reference_rejected(self):
        b=ET.fromstring(b'<block><outputs><port name="result">missing[0].Y[0]-&gt;m</port></outputs></block>')
        with self.assertRaises(ValueError):output_net(b,'result',0)

    def fixture(self,capacity):
        nodes=''.join(f'<node id="{i}" type="{t}" capacity="{c}"><loc xlow="2" ylow="2" xhigh="2" yhigh="2" layer="0" ptc="{p}"/></node>'
                      for i,t,c,p in [(0,'SOURCE',2,0),(1,'OPIN',1,0),(2,'OPIN',1,1),(3,'CHANX',capacity,0)])
        return f'''<rr_graph><block_types><block_type id="0" name="complex_dsp"><pin_class type="OUTPUT"><pin ptc="0">complex_dsp.result[0]</pin><pin ptc="1">complex_dsp.result[1]</pin></pin_class></block_type></block_types><grid><grid_loc x="2" y="2" layer="0" block_type_id="0"/></grid><rr_nodes>{nodes}</rr_nodes><rr_edges><edge src_node="0" sink_node="1"/><edge src_node="0" sink_node="2"/><edge src_node="1" sink_node="3"/><edge src_node="2" sink_node="3"/></rr_edges></rr_graph>'''

    def test_shared_exit_not_counted_twice(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/'g.xml';path.write_text(self.fixture(1))
            groups=[{'case':'synthetic','coordinate':(2,2,0),'nets':[{'bit':0,'net':'a'},{'bit':1,'net':'b'}]}]
            d=prove(path,groups);self.assertEqual(d['certificates'][0]['demand'],2);self.assertEqual(d['certificates'][0]['capacity'],1)

    def test_capacity_and_equivalent_class_expansion(self):
        with tempfile.TemporaryDirectory() as t:
            path=Path(t)/'g.xml';path.write_text(self.fixture(2))
            groups=[{'case':'synthetic','coordinate':(2,2,0),'nets':[{'bit':0,'net':'a'},{'bit':1,'net':'b'}]}]
            self.assertFalse(prove(path,groups)['certificates'])
            path.write_text(self.fixture(1));groups[0]['nets'][1]['net']='a'
            self.assertFalse(prove(path,groups)['certificates'])


if __name__=='__main__':unittest.main()
