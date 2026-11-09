"""Failed partial routes must never enter the paired timing denominator."""
import math
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from collect_three_baselines import paired_cpd, refined_failure


def row(case, arm, value, valid=True):
    return dict(case=case, arm=arm, cpd_ns=value, valid_solution=valid)


class PairingTests(unittest.TestCase):
    def test_capacity_failure_refined_without_mutating_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory)/'stdout.log').write_text('Failed to find device which satisfies resource requirements required: clb: 23877 (available clb: 14308)')
            job=dict(directory=directory,state='finished',classification='tool_or_input_failure')
            self.assertEqual(refined_failure(job),'device_capacity_failure')
            self.assertEqual(job['classification'],'tool_or_input_failure')

    def test_failed_estimates_and_missing_runs_are_excluded(self):
        rows=[row('x','a0',10),row('x','a3',8),row('y','a0',10),row('y','a3',1,False),row('z','a0',10)]
        result=paired_cpd(rows,'a0','a3')
        self.assertEqual(result['registered_cases'],3)
        self.assertEqual(result['paired_legal_cases'],1)
        self.assertEqual(result['excluded_cases'],['y','z'])
        self.assertAlmostEqual(result['cpd_change_percent'],-20)

    def test_geomean_uses_matched_ratios(self):
        rows=[row('x','a0',10),row('x','a3',8),row('y','a0',20),row('y','a3',25)]
        self.assertAlmostEqual(paired_cpd(rows,'a0','a3')['cpd_geomean_ratio'],1)

    def test_no_common_success_is_not_zero_improvement(self):
        result=paired_cpd([row('x','a0',10),row('x','a3',9,False)],'a0','a3')
        self.assertIsNone(result['cpd_geomean_ratio'])

    def test_reject_invalid_successful_metric_and_duplicate_pairs(self):
        for value in (None,0,-1,math.inf,math.nan):
            with self.subTest(value=value),self.assertRaises(ValueError):
                paired_cpd([row('x','a0',10),row('x','a3',value)],'a0','a3')
        with self.assertRaises(ValueError):
            paired_cpd([row('x','a0',10),row('x','a0',12)],'a0','a3')


if __name__=='__main__':
    unittest.main()
