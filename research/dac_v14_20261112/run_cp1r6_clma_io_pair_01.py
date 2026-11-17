"""Single serial owner for the preregistered clma_io native/domain pair."""
import fcntl
import os
import time
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity
from cp1r6_clma_io_cohort_01 import ROOT, execute


def main():
    queue = ROOT/'queue'
    queue.mkdir(exist_ok=False)
    owner = process_identity(os.getpid())
    write(queue/'registration.json', dict(**owner, plan=str(ROOT/'plan.json'),
          plan_sha256=sha(ROOT/'plan.json'), ownership='Only registered CP1r6 clma_io pair owner'))
    write(queue/'status.json', dict(status='waiting_for_shared_serial_slot'))
    with (D/'critical_scope_runner.lock').open('r') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        plan = read(ROOT/'plan.json')
        assert all(sha(p)==h for p,h in plan['source_sha256'].items())
        assert read(D/'confirmation_release_cp1r6_01/public_source_reconstruction.json')['passed']
        started = time.monotonic()
        try:
            execute(plan)
            comparison = read(ROOT/'comparison.json')
            write(queue/'completion.json', dict(passed=True, status='registered_clma_io_pair_terminal',
                  scientific_quality_admitted_roles=comparison['verified_legal_roles'],
                  complete_queue_scope_seconds=time.monotonic()-started,
                  comparison=str(ROOT/'comparison.json'),
                  qualification='All two registered roles accounted; execution terminal is distinct from scientific admission. No research completion condition.'))
            write(queue/'status.json', dict(status='terminal'))
        except BaseException as error:
            write(queue/'completion.json', dict(passed=False, status='clma_io_owner_requires_reconciliation',
                  error=repr(error), complete_queue_scope_seconds=time.monotonic()-started,
                  automatic_retry=False, original_receipts_preserved=True))
            write(queue/'status.json', dict(status='terminal_reconciliation_required'))
            raise


if __name__=='__main__':
    main()
