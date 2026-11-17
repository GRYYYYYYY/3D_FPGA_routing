"""Freeze extra evidence gates without changing six-role confirmation rules."""
import sys
from datetime import datetime,timezone
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
import cp1r3_raw_admission_v1 as gate

root=gate.ROOT;assert not root.exists()
supp=read(gate.SUPPLEMENT/'plan.json');cohort=read(gate.COHORT/'plan.json')
validation=[D/'CP1r3_raw_admission_validation_01/validation.json',D/'CP1r3_raw_state_schema_validation_01/validation.json']
for p in validation:
    v=read(p);assert v['passed'] and all(sha(f)==h for f,h in v['source_sha256'].items())
sources={Path(m.__file__).resolve() for m in list(sys.modules.values())
    if getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(D)}
sources.update([Path(__file__).resolve(),D/'queue_cp1r3_raw_admission_priority_04.py',
    gate.SUPPLEMENT/'plan.json',gate.COHORT/'plan.json',Path(cohort['release'])/'runtime/runtime_metrics.py',*validation])
for p in sources:assert p.stat().st_size<2*1024**2
root.mkdir()
write(root/'plan.json',dict(registered_at=datetime.now(timezone.utc).isoformat(),targets=supp['targets'],
    release=cohort['release'],release_manifest_sha256=cohort['release_manifest_sha256'],
    source_sha256={str(p):sha(p) for p in sorted(sources)},
    predecessor=str(gate.SUPPLEMENT/'queue_priority_03'),
    actual_execution_requires_original_cohort_and_supplement_terminal_and_dead=True,
    actual_execution_requires_exclusive_shared_serial_lock=True,new_native_or_STA_calls=0,
    original_results_readonly=True,accepted_policy_and_method_changed=False,
    actual_observation='LSTM/native ended with original seal-verifier failure; LSTM/domain active; other four roles unstarted.',
    gates=['original full frozen checks plus exact owner binding transition',
        'actual shared inputs, graph artifacts and original output bytes',
        'complete serialized request and ordered actual QUERY/ATTEMPT/COMPLETE logs, including failed prefix',
        'raw FULL and complete raw STA versus full exact stored endpoint vector',
        'original physical proof graph/route binding; explicit same-byte proof reuse',
        'owner installed candidate callback, restored source and serialized physical proof provenance',
        'whole measured command cost distinct from every research audit cost',
        'paired actual packed/placement/initial route/full endpoint vector and six graph payloads'],
    known_scope='Original physical proof is byte-revalidated, not rerun; unsupported schemas fail closed and require an explicit supplemental amendment. No repeat of native queries.',
    paper_changes_after_admission='Only related input rows, applicability, abstract and conclusions; no automatic method rewrite.',
    ETA='No calibrated duration for actual raw audits. Measure each role and whole audit separately.',
    complete_research_goal=False))
print(dict(registered=True,targets=len(supp['targets']),source_bindings=len(sources),native_calls=0))
