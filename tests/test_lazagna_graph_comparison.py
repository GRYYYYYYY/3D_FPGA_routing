"""Ensure graph comparison detects missing edges despite node renumbering."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from compare_lazagna_graphs import compare


class ExactGraphComparison(unittest.TestCase):
    def graph(self,order,edges):
        nodekeys=[('OPIN',(2,2,0),(2,2,0),74,'LEFT','NONE',''),
                  ('CHANY',(1,1,0),(1,4,0),0,'','INC_DIR','L4'),
                  ('IPIN',(2,4,0),(2,4,0),0,'LEFT','NONE','')]
        ids={original:new for new,original in enumerate(order)}
        return dict(keys=[nodekeys[i] for i in order],kinds=[nodekeys[i][0] for i in order],
                    caps=[1,1,1],switches={7:dict(name='mux')},
                    edges=[(ids[u],ids[v],7) for u,v in edges])

    def test_node_renumbering_preserves_equivalence(self):
        a=self.graph([0,1,2],[(0,1),(1,2)]);b=self.graph([2,0,1],[(0,1),(1,2)])
        self.assertTrue(compare(a,b)['identical_planar_topology'])

    def test_missing_exit_detected(self):
        a=self.graph([0,1,2],[(0,1),(1,2)]);b=self.graph([2,0,1],[(1,2)])
        r=compare(a,b)
        self.assertFalse(r['identical_planar_topology']);self.assertEqual(r['only_left_edges'],1)
        self.assertEqual(r['left_only_examples'][0]['source'][0],'OPIN')

    def test_reversed_edge_detected(self):
        a=self.graph([0,1,2],[(0,1),(1,2)]);b=self.graph([2,0,1],[(1,0),(1,2)])
        r=compare(a,b);self.assertEqual(r['only_left_edges'],1);self.assertEqual(r['only_right_edges'],1)

    def test_capacity_change_detected(self):
        a=self.graph([0,1,2],[(0,1)]);b=self.graph([2,0,1],[(0,1)])
        b['caps'][2]=2
        self.assertEqual(compare(a,b)['capacity_mismatches'],1)


if __name__=='__main__':unittest.main()
