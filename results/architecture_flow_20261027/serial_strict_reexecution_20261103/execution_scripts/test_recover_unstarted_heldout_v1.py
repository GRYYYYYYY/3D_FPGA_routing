import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import recover_unstarted_heldout_v1 as recovery

class UnstartedRecoveryTest(unittest.TestCase):
    def test_preserves_unstarted_after_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp); folder=base/'evaluation_invocations'; folder.mkdir()
            jobs=[dict(phase='heldout',circuit='c',seed=i,family='sb',width=100) for i in (21,23)]
            (base/'evaluation_jobs.json').write_text(json.dumps({'jobs':jobs}))
            prior=folder/'heldout_all_s0.json'; prior.write_text(json.dumps({'phase':'heldout','unstarted_jobs':jobs}))
            prior_bytes=prior.read_bytes()
            def execute(selected, workers):
                self.assertEqual(selected,jobs); self.assertEqual(workers,1)
                return ([dict(status='error',job=jobs[0])],[jobs[1]])
            with patch.object(recovery,'BASE',base), patch.object(recovery.evaluation,'register',return_value={'jobs':jobs}), \
                 patch.object(recovery.evaluation,'execute_cases',side_effect=execute), \
                 patch.object(recovery.evaluation.io,'seal_inputs'):
                with self.assertRaisesRegex(RuntimeError,'requires diagnosis'): recovery.main(1)
            output=json.loads((folder/'heldout_unstarted_recovery_v1_1.json').read_text())
            self.assertEqual(output['unstarted_jobs'],[jobs[1]])
            self.assertEqual(prior.read_bytes(),prior_bytes)
            self.assertTrue((folder/'heldout_unstarted_recovery_v1_1_registration.json').exists())

if __name__ == '__main__': unittest.main()
