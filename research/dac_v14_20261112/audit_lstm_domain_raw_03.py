"""Full original raw audit plus a narrow, rejected failed-evaluation proof.

No historical completion view is manufactured. The native fallback traverses
the original parser, source checks, candidate checks and domain checks.
"""
import fcntl
import time
import traceback
from pathlib import Path
import cp1r3_raw_admission_v1 as original
from lstm_failed_scope_audit_v1 import KnownFailedScope,EVALUATION,transformed_raw_transaction
from retained_prefix_workflow import D,read,write
from recovery_prefix_v1 import Evidence


def main():
    root=D/'LSTM_domain_whole_admission_03'
    output=root/'raw'
    assert not output.exists()
    with (D/'critical_scope_runner.lock').open('r') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        output.mkdir()
        started=time.monotonic();evidence=Evidence()
        plan=read(root/'execution_plan.json');evidence.bind(root/'execution_plan.json')
        evidence.verify(plan['source_sha256'])
        original.SUPPLEMENT=D/'CP1r3_supplemental_verifier_03'
        transaction,shape=transformed_raw_transaction(original)
        class FullDomainAudit(original.Audit):
            def __init__(self,release,e):
                super().__init__(release,e)
                self.failed_scope=KnownFailedScope(plan['failed_candidate_audit_sha256'],e)
            def state(self,state,flow):
                resolved=str(Path(state).resolve())
                if resolved==str(EVALUATION):
                    if resolved not in self.states:
                        self.states[resolved]=self.failed_scope.rejected_state(state,flow)
                    return self.states[resolved]
                return super().state(state,flow)
        FullDomainAudit.transaction=transaction
        audit=FullDomainAudit(plan['release'],evidence)
        try:
            target=plan['domain_target']
            old=read(original.COHORT/'lstm_results.json')['domain']
            row=audit.case(target,old,output)
            evidence.unchanged()
            assert audit.failed_scope.loaded
        except Exception:
            error=traceback.format_exc();(output/'failure.log').write_text(error)
            row=dict(passed=False,status='independent_full_domain_raw_admission_failed',
                     quality_admitted=False,quality=None,error=error,
                     original_failures_preserved=True,new_native_or_STA_calls=0)
        row.update(complete_additional_readonly_seconds=time.monotonic()-started,
                   source_sha256=evidence.bound,raw_transform=shape,
                   failed_scope_events=audit.failed_scope.events,
                   historical_false_completion_rewritten=False,
                   failed_candidate_adopted_to_controller=False,
                   original_physical_proofs_revalidated=True,new_physical_solver_executions=0,
                   formal_complete_time_ratio=None,automatic_paper_update=False,
                   qualification='Normal original raw gates plus one explicitly rejected failed evaluation backed by completed independent raw audit and fresh byte closure. Historical failure and native fallback preserved. Complete domain quality requires all remaining original gates; paired matching is separate. Original full attempt includes ctime incident and is not clean interleaved overhead.')
        write(output/'completion.json',row)
        assert row['passed'],row.get('error')


if __name__=='__main__':
    main()
