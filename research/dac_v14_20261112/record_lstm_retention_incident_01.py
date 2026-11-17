"""Record existing receipt evidence of the retention ctime incident; no native work."""
import datetime
import hashlib
import json
from pathlib import Path

D = Path(__file__).resolve().parent
OUT = D / 'LSTM_retention_metadata_incident_01'
R = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_workspaces/cp1r3_distinct_input_cohort_01/lstm/domain/flow/resource_flow/repair/round_013/candidate_00')
E = R / 'reuse_on_evaluation'
OUT.mkdir(exist_ok=False)
evidence = {}

def read(path):
    # Copy bounded metadata to distinct new files; never link/chmod source inodes.
    assert path.stat().st_size < 100000, path
    data = path.read_bytes()
    name = str(path.relative_to(R)) if path.is_relative_to(R) else path.name
    copy = OUT / 'receipts' / name
    copy.parent.mkdir(parents=True, exist_ok=True)
    copy.write_bytes(data)
    evidence[str(path)] = dict(sha256=hashlib.sha256(data).hexdigest(), copy=str(copy.relative_to(D)), bytes=len(data))
    return json.loads(data)

seal = read(E / 'input_seal.json')
registration = read(E / 'registration.json')
prior = read(R / 'reuse_on/input_seal.json')
physical = read(E / 'independent_native_analysis_audit.json')
manifest = read(E / 'runs/state/manifest.json')
supervision = read(R / 'reuse_on_FULL_STA_supervision.json')
transaction = read(R / 'completion.json')
inventory = read(D / 'LSTM_existing_tradeoffs_02/retained_payload_inventory.json')
indexed = {row['original']: row for row in inventory['files']}
rows = []
for path, item in seal['inputs'].items():
    if item['passed']:
        continue
    old = prior['inputs'][path]
    retained = indexed[path]
    a, b = Path(path).stat(), Path(retained['retained']).stat()
    rows.append(dict(
        path=path, retained_path=retained['retained'],
        original_registration_sha256=registration['source_sha256'][path],
        final_rehash_sha256=item['sha256'],
        byte_digest_matches_registration=item['sha256'] == registration['source_sha256'][path],
        prior_successful_seal=old,
        failed_final_seal=item,
        prior_device_inode_size_mtime_unchanged=old['stat_identity'][:4] == item['stat_identity'][:4],
        ctime_changed=old['stat_identity'][4] != item['stat_identity'][4],
        retained_inode_matches_failure=(retained['device'], retained['inode']) == tuple(item['stat_identity'][:2]),
        current_link_identity_matches=(a.st_dev,a.st_ino) == (b.st_dev,b.st_ino) == (retained['device'],retained['inode']),
        current_ctime_still_matches_failed_seal=a.st_ctime_ns == item['stat_identity'][4],
        changed_utc=datetime.datetime.fromtimestamp(item['stat_identity'][4]/1e9,datetime.timezone.utc).isoformat()))
checks = dict(
    exactly_five_stat_failures=len(rows)==5,
    all_registered_digests_match_existing_final_rehash=all(seal['inputs'][p]['sha256']==h for p,h in registration['source_sha256'].items()),
    five_failures_have_unchanged_bytes_and_only_ctime_difference=all(all(row[k] for k in ['byte_digest_matches_registration','prior_device_inode_size_mtime_unchanged','ctime_changed','retained_inode_matches_failure','current_link_identity_matches','current_ctime_still_matches_failed_seal']) for row in rows),
    original_seal_failed=seal['passed'] is False,
    actual_native_completed=manifest['status']=='completed' and manifest['returncode']==0,
    physical_audit_passed=physical['passed'] is True,
    wrapper_failed=supervision['returncode']==1 and supervision['passed'] is False,
    original_controller_failure_preserved=transaction['roles']['reuse_on']['status']=='FULL_STA_failed',
    no_synthetic_completion_or_gate=not (E/'completion.json').exists() and not (E/'runs/state/analysis_gate.json').exists(),
)
assert all(checks.values()), checks
result = dict(
    status='incident_evidence_recorded_not_candidate_admission', observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    cause='Agent archival os.link changed ctime of five source files while a downstream evaluation held their frozen identities.',
    classification='infrastructure_input_metadata_interference',
    responsible_action=str(D/'analyze_lstm_existing_tradeoffs_01.py'),
    registered_hashes_compared=len(registration['source_sha256']), sealed_inputs=len(seal['inputs']),
    checks=checks, failed_inputs=rows, source_evidence=evidence,
    original_seal_utc=seal['utc'], native_complete_seconds=manifest['wall_seconds'],
    failed_evaluation_supervision_seconds=supervision['complete_seconds'],
    whole_transaction_seconds=transaction['complete_orchestrator_seconds'],
    costs_qualification='Nested measured scopes, not additive. Original whole-role measurement must retain the failed evaluation. This intervened run cannot establish clean matched algorithm overhead.',
    raw_physical_observation=physical['legal'][0]['physical_metrics'],
    acceptance_qualification='No candidate admission or endpoint/STA completion is synthesized. Physical receipt reports wire2390832, 419SB, 8316CB, outside the unchanged2390475 cap by357; that arithmetic is not a newly executed policy decision. This is distinct from the retained round012/candidate02 419SB point at wire2390877, rejected by402.',
    original_native_fallback=transaction['roles']['reuse_off'],
    operational_resolution='Preserve all original files, ctimes, failures and actual fallback trajectory. Do not create/remove hardlinks, chmod, touch or replace any live upstream inputs. Further archival must use separate copied bytes under the serial slot, or defer; existing links remain untouched. No source, running rule, queue or budget changes.',
    admission_followup='At existing supplemental/raw admission review, keep this failed stage excluded; attribute it to infrastructure, not infeasible routing. Reuse existing outputs for any independent audit, never rewrite historical completion or repeat native search. Do not infer a counterfactual controller trajectory.',
    paper_impact='No established paper result changes. Pending LSTM quality/pair admission and clean timing applicability require this incident disclosure; no complete CP1r3 benefit or ratio is claimed.',
    new_native_calls=0, new_STA_calls=0, new_large_input_hashes=0)
(OUT/'incident.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(output=str(OUT),checks=checks,failed_inputs=len(rows),registered_hashes_compared=len(registration['source_sha256'])),indent=2))
