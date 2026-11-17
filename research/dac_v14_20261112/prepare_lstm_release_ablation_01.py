"""One same-source causal intervention, reusing the frozen transaction/audit path."""
from pathlib import Path
import json,hashlib,copy,difflib,datetime
D=Path(__file__).resolve().parent
F=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/confirmation_releases/current_sta_cp1r3/runtime')
B=D/'LSTM_release_ablation_01';B.mkdir(exist_ok=False)
def read(p):return json.loads(Path(p).read_text())
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
rows=read(D/'LSTM_admitted_mechanism_synthesis_01/accepted_steps.json')
r=next(x for x in rows if x['arm']=='domain' and x['release_event_count']>0)
assert r['id']=='domain/round_001/candidate_00/reuse_on' and r['raw_route_evidence_passed']
assert read(D/'LSTM_domain_whole_admission_03/admission_decision.json')['complete_pair_admission']=='passed'
reference=Path(r['transaction']);reg=read(reference/'registration.json');old=reg['roles']['reuse_on'];role=copy.deepcopy(old)
assert role['domain_failure_release'] and role['crossing_reuse_enabled'] and len(role['queries'])==8
# Distinct output; existing physical inputs and source are read-only, unchanged.
for k,n in [('request','request.txt'),('crossing_domain','domain.txt')]:
 (B/n).write_bytes(Path(role[k]).read_bytes());role[k]=str(B/n);role['source_sha256'][str(B/n)]=sha(B/n)
role['domain_failure_release']=False
reg['roles']={'reuse_on':role};reg['execution_policy']='single_registered_resource_scope'
original=F/'run_serial_lazy_resource_transactions_stream_v1.py';s=original.read_text()
old_block="assert reg['execution_policy']=='domain_first_stop_on_resource_accept'\nfor name in execution_order(reg['roles']):"
new_block="assert reg['execution_policy']=='single_registered_resource_scope'\nassert set(reg['roles'])=={'reuse_on'}\nfor name in reg['roles']:"
assert s.count(old_block)==1
adapter=B/'run_single_registered_scope.py'
# Only bootstrap locates the unchanged frozen runtime; scheduling selects one role.
bootstrap='import sys\nsys.path.insert(0, '+repr(str(F))+')\n'
adapter.write_text(bootstrap+s.replace(old_block,new_block))
assert adapter.read_text()[len(bootstrap):].replace(new_block,old_block)==s
(B/'adapter.diff').write_text(''.join(difflib.unified_diff(s.splitlines(True),adapter.read_text().splitlines(True),fromfile=str(original),tofile=str(adapter))))
reg['source_sha256'][str(adapter)]=sha(adapter)
write(B/'prepared_transaction_registration.json',reg)
files=[Path(__file__).resolve(),original,adapter,F/'artifact_manifest.json',D/'LSTM_admitted_mechanism_synthesis_01/accepted_steps.json',D/'LSTM_domain_whole_admission_03/admission_decision.json',reference/'registration.json',reference/'completion.json',reference/'reuse_on_audit/analysis.json',reference/'reuse_on_domain_audit.json',B/'request.txt',B/'domain.txt',B/'prepared_transaction_registration.json']
plan=dict(registered_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),reference_transaction=str(reference),reference_accepted_step=r,selection_rule='Earliest committed guided group with at least one release event in the admitted LSTM trajectory. Retrospective mechanism selection, not held-out confirmation or outcome cherry-picking among new runs.',frozen_runtime=str(F),native_repair_workers_planned=1,candidate_FULL_STA_if_new_legal_route=True,existing_release_candidate_reused=True,only_algorithm_flag_changed='domain_failure_release: true -> false',original_algorithm_and_artifacts_mutated=False,source_sha256={str(p):sha(p) for p in files},scope='One imported same-source transaction. Preserve all failures/no-gain/rejections, exact source restoration, original budgets/physical delays, native FULL/STA and existing physical/domain audits. No whole-flow speed ratio or all-LSTM causal attribution. No previous completed request is rerun under the same treatment; the no-release treatment is new. No frozen confirmation version changed.')
write(B/'plan.json',plan)
write(B/'preflight.json',dict(passed=True,single_role_adapter_changes_only_bootstrap_and_scheduling=True,request_and_domain_bytes_exact=True,all_eight_queries_and_source_preserved=True,budget_and_acceptance_unchanged=True,native_calls_new=0))
print(dict(registered=str(B/'plan.json'),selected=r['id'],existing_release_delta=r['source_resource_delta']))
