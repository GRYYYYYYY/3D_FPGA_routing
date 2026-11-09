import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import recover_evaluation_case_v1 as recovery

class RecoveryTest(unittest.TestCase):
    def run_case(self, fail_audit=False):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp); name = 'heldout_c_s21_sb_w100'; case = base/'evaluation_cases'/name
            case.mkdir(parents=True); (base/'runs').mkdir()
            job = dict(phase='heldout', circuit='c', seed=21, family='sb', width=100,
                       roles={'p0':{'A0':dict(router='A0',variant=None,config=None),
                                    'duplicate':dict(router='A0',variant=None,config=None)}})
            original = dict(status='error', error='Free space below evaluation reserve: test', job=job, flows={})
            (case/'result.json').write_text(json.dumps(original))
            (base/'selected_configs.json').write_text('{}')
            (base/'benchmark_protocol.json').write_text('{}')
            (base/'execution_resource_amendment.json').write_text('{}')
            (base/'evaluation_jobs.json').write_text(json.dumps({'jobs':[job],
                'protocol_sha256':recovery.sha256(base/'benchmark_protocol.json'),
                'selection_sha256':recovery.sha256(base/'selected_configs.json'),
                'resource_amendment_sha256':recovery.sha256(base/'execution_resource_amendment.json'),
                'shared_source_sha256':{}}))
            (case/'registration.json').write_text(json.dumps(dict(jobs_sha256=recovery.sha256(base/'evaluation_jobs.json'),
                selection_sha256=recovery.sha256(base/'selected_configs.json'))))
            calls = []
            def route(*args): calls.append(args); return {'name':'existing', 'status':'failed'}
            def audit(ctx, receipts, path):
                if fail_audit: raise RuntimeError('audit failed')
                recovery.write_json(path, {'passed':True}); return {'legal_count':0,'failed_count':1}
            def compact(receipts, path): recovery.write_json(path, {'groups':[], 'saved_bytes':0})
            with patch.object(recovery,'BASE',base), patch.object(recovery.study,'context',return_value={}), \
                 patch.object(recovery.study,'placement',return_value={'status':'completed'}), \
                 patch.object(recovery.study,'route',side_effect=route), \
                 patch.object(recovery.study,'audit_batch',side_effect=audit), \
                 patch.object(recovery.evaluation,'compact_completed_route_inputs',side_effect=compact), \
                 patch.object(recovery.evaluation.io,'seal_inputs'), \
                 patch.object(recovery.evaluation,'require_disk_space'):
                if fail_audit:
                    with self.assertRaisesRegex(RuntimeError, 'audit failed'): recovery.main(name)
                else: recovery.main(name)
            self.assertEqual(len(calls),1)
            self.assertEqual(json.loads((case/'recovery_disk_reserve_v1/original_result.json').read_text()),original)
            result=json.loads((case/'result.json').read_text())
            if fail_audit: self.assertEqual(result,original)
            else:
                self.assertEqual(result['status'],'completed')
                self.assertEqual(result['flows']['p0']['roles'],{'A0':'existing','duplicate':'existing'})

    def test_publish_after_audit_and_reuse_duplicate_role(self): self.run_case()
    def test_failed_audit_preserves_original(self): self.run_case(True)

if __name__ == '__main__': unittest.main()
