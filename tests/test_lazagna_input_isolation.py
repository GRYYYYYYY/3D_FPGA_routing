"""Protect a shared placement when historical VPR rewrites its loaded input."""
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import run_lazagna_routes as lr


class FixedInputIsolation(unittest.TestCase):
    def test_solver_rewrite_cannot_modify_shared_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);base=root/'results';primary=base/'primary';primary.mkdir(parents=True)
            (primary/'packed.net').write_text('packed-netlist')
            (primary/'fixed.place').write_text('original-placement')
            graph=base/'rr.xml';graph.write_text('rr-graph')
            job=dict(name='paper_fixed_case_w100_i200',case='case',family='paper',width=100,arm='fixed')
            def fake_run(name,command,**kwargs):
                place=Path(command[command.index('--place_file')+1])
                packed=Path(command[command.index('--net_file')+1])
                self.assertNotEqual(place,primary/'fixed.place')
                self.assertEqual(place.read_bytes(),(primary/'fixed.place').read_bytes())
                self.assertEqual(packed.read_bytes(),(primary/'packed.net').read_bytes())
                self.assertIn(primary/'fixed.place',kwargs['inputs'])
                self.assertIn(place,kwargs['inputs'])
                place.write_text('solver-rewrite')
                (place.parent/'stdout.log').write_text('test stopped')
                return {'status':'failed'}
            with patch.object(lr,'ROOT',root),patch.object(lr,'BASE',base),patch.object(lr,'graph_job',return_value={'graph':str(graph)}),patch.object(lr,'run',side_effect=fake_run):
                lr.run_one(job,{'directory':str(primary)})
                self.assertEqual((primary/'fixed.place').read_text(),'original-placement')
                self.assertEqual((primary/'packed.net').read_text(),'packed-netlist')
                with self.assertRaises(RuntimeError):lr.run_one(job,{'directory':str(primary)})


if __name__=='__main__':unittest.main()
