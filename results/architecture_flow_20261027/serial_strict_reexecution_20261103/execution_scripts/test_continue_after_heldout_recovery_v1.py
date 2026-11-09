"""Verify evidence gates and stop-on-error sequencing without solver runs."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import continue_after_heldout_recovery_v1 as continuation


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


class ContinuationTest(unittest.TestCase):
    def fixture(self, base):
        job = dict(phase='heldout', circuit='c', seed=21, family='sb', width=100,
                   roles={'p0': {'A0': {}, 'R1': {}}})
        write(base / 'evaluation_jobs.json', {'jobs': [job]})
        directory = base / 'evaluation_cases' / 'heldout_c_s21_sb_w100'
        row = dict(status='completed', roles={'A0': 'a0', 'R1': 'r1'},
                   registered_roles=2, unique_runs=2, legal_runs=0, failed_runs=2)
        result = dict(status='completed', job=job, flows={'p0': row})
        write(directory / 'result.json', result)
        write(directory / 'p0_audit_summary.json', dict(passed=True, registered_route_count=2,
            legal_count=0, failed_count=2, legal=[], failed=[{'name': 'a0'}, {'name': 'r1'}]))
        return directory, result

    def test_failed_routes_are_accounted_but_missing_roles_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            directory, result = self.fixture(base)
            with patch.object(continuation, 'BASE', base), patch.object(continuation, 'HELDOUT_COUNT', 1):
                self.assertEqual(continuation.heldout_gate(), 1)
                del result['flows']['p0']['roles']['R1']
                write(directory / 'result.json', result)
                with self.assertRaises(AssertionError):
                    continuation.heldout_gate()

    def test_unfinished_case_and_mismatched_audit_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            directory, result = self.fixture(base)
            with patch.object(continuation, 'BASE', base), patch.object(continuation, 'HELDOUT_COUNT', 1):
                result['status'] = 'error'
                write(directory / 'result.json', result)
                with self.assertRaises(AssertionError):
                    continuation.heldout_gate()
                result['status'] = 'completed'
                write(directory / 'result.json', result)
                audit = continuation.read(directory / 'p0_audit_summary.json')
                audit['failed'][1]['name'] = 'unrelated'
                write(directory / 'p0_audit_summary.json', audit)
                with self.assertRaises(AssertionError):
                    continuation.heldout_gate()

    def test_full_sequence_and_child_failure_stop(self):
        for fail in (False, True):
            with self.subTest(fail=fail), tempfile.TemporaryDirectory() as tmp:
                completed, calls = [], []
                def run(cmd, **kwargs):
                    calls.append(Path(cmd[1]).name)
                    if fail and len(calls) == 2:
                        raise subprocess.CalledProcessError(1, cmd)
                with patch.object(continuation.original, 'verify'), \
                     patch.object(continuation.original, 'quiescent'), \
                     patch.object(continuation.evaluation, 'require_disk_space'), \
                     patch.object(continuation.subprocess, 'run', side_effect=run):
                    if fail:
                        with self.assertRaises(subprocess.CalledProcessError):
                            continuation.execute_stages(Path(tmp), {}, lambda *a, **k: None, completed)
                        self.assertEqual(completed, ['width300'])
                        self.assertEqual(len(calls), 2)
                    else:
                        continuation.execute_stages(Path(tmp), {}, lambda *a, **k: None, completed)
                        self.assertEqual(completed, [label for label, _ in continuation.STAGES])
                        self.assertEqual(calls[-1], 'analyze_paired_width_diagnostic.py')


if __name__ == '__main__':
    unittest.main()
