"""Consume the original full raw admission checks after the repaired output replay.

Only the supplemental result namespace is relocated. Original Audit methods,
source plan, complete ordered requests, raw vectors and physical gates stay
unchanged; failures remain null and no native/STA subprocess is run.
"""
import fcntl
import resource
import time
import traceback
from pathlib import Path
import cp1r3_raw_admission_v1 as original
from retained_prefix_workflow import D, read, write
from recovery_prefix_v1 import Evidence


def main():
    root=D/'LSTM_necessary_readonly_02'
    output=root/'native_raw'
    assert not output.exists()
    with (D/'critical_scope_runner.lock').open('r') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        output.mkdir()
        started=time.monotonic()
        evidence=Evidence()
        plan=read(root/'execution_plan.json')
        evidence.bind(root/'execution_plan.json')
        evidence.verify(plan['source_sha256'])
        original.SUPPLEMENT=D/'CP1r3_supplemental_verifier_02'
        target=plan['native_target']
        result=read(original.COHORT/'lstm_results.json')['native']
        try:
            row=original.Audit(plan['release'],evidence).case(target,result,output)
            evidence.unchanged()
        except Exception:
            error=traceback.format_exc()
            (output/'failure.log').write_text(error)
            row=dict(passed=False,status='additional_raw_admission_failed',
                     quality_admitted=False,quality=None,error=error,
                     original_failures_preserved=True,new_native_or_STA_calls=0)
        row.update(complete_additional_readonly_seconds=time.monotonic()-started,
                   process_max_RSS_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                   source_sha256=evidence.bound,
                   original_raw_Audit_methods_unchanged=True,
                   original_supplemental_and_raw_failures_unchanged=True,
                   full_native_domain_pair_admitted=False,
                   automatic_paper_claim_update=False)
        write(output/'completion.json',row)
        assert row['passed'],row.get('error')


if __name__=='__main__':
    main()
