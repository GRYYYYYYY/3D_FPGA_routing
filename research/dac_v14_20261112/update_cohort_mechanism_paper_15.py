"""Integrate closed confirmation and verified union ablation, without rerouting."""
from pathlib import Path
import shutil
from retained_prefix_workflow import D,read,write,sha

parent_path=D/'CP1r2_pair_paper_binding_14.json';parent=read(parent_path)
previous=Path(parent['snapshot']);p=D/'paper';e=D/'cohort_mechanism_paper_evidence_15'
assert not e.exists();e.mkdir()
assert sha(p/'current_repair_main.tex')==sha(previous/'current_repair_main.tex')
cohort_path=D/'cp1r2_cross_circuit_cohort_01/terminal_evidence_01/completion.json'
union_path=D/'robot_union_mechanism_02/verification_v2.json'
owner_path=D/'robot_owner_reentry_audit_02/completion.json'
c=read(cohort_path);u=read(union_path);o=read(owner_path)
assert c['passed'] and c['registered_roles']==4 and c['verified_legal_roles']==2 and c['initial_execution_timeouts']==2
assert u['passed'] and o['passed'] and o['existing_reload_exact_identity']['passed']
rows=[]
for arm,label in [('native','N'),('domain','D')]:
    r=c['outcomes']['tpu_ws']['arms'][arm]
    assert r['classification']=='initial_routing_execution_timeout' and r['quality'] is None
    rows.append(f"TPU CP1r2 {label} (initial timeout)&--&--&{r['complete_attempt_seconds']:.2f}&{r['sampled_PSS_kib']/1048576:.3f}&--"+r'\\')
union_rows=[];summary={}
for role,label in [('union_native','Robot union N'),('union_domain_no_release','Robot union D/no release'),('union_domain_release','Robot union D/release')]:
    r=u['outcomes'][role];q=r['quality'];ep=r.get('endpoint_comparison')
    assert not r['committed_to_original_actor']
    vals='--&--' if q is None else f"{q['CPD_ns']:.6f}&{q['resources']['wirelength']}/{q['resources']['SB_pairs']}/{q['resources']['CB_sources']}"
    endpoint='--' if ep is None else f"{ep['setup_improved']}/{ep['setup_regressed']}/{ep['hold_violation_regressions']}"
    union_rows.append(label+r'$^{\S}$&'+vals+'&--&--&'+endpoint+r'\\')
    summary[role]={k:r[k] for k in ['status','quality','native_core_seconds','actual_queries','actual_attempts','committed_to_original_actor']}
    summary[role]['endpoint_summary']=None if ep is None else {k:v for k,v in ep.items() if k!='changes'}
    summary[role]['resource_accepted']=r.get('resource_policy_decision',{}).get('accepted')
assert summary['union_native']['resource_accepted'] is False
assert summary['union_domain_release']['resource_accepted'] is True
old=(previous/'current_repair_main.tex').read_text();new=old
new=new.replace('Supervision interrupted (5 arms)','\n'.join(rows)+'\nSupervision interrupted (5 arms)')
anchor='Robot owner $\\Delta^{\\ddagger}$&0&+12/0/+1&155.10&2.340&31/0/0'+r'\\\hline'
assert new.count(anchor)==1
new=new.replace(anchor,anchor.replace(r'\hline','')+'\n'+'\n'.join(union_rows)+r'\hline')
new=new.replace('shared pair cost/PSS.}',r'shared pair cost/PSS. $^{\S}$Same-source union: shared three-arm command 194.52 s, 2.342 GiB; no standalone per-arm cost.}')
new=new.replace('Table~\\ref{tab:completecost} retains 34 complete attempts (four routing and four loading failures), five supervision-interrupted and four pre-native launch failures (two grouped rows), and two scoped components; the owner row reports paired deltas and shared cost.', 'Table~\\ref{tab:completecost} retains 36 terminal attempts (four routing failures, four loading failures, two initial execution timeouts), nine infrastructure failures in two grouped rows, and five scoped components. Shared component costs are not assigned to individual arms.')
new=new.replace('A prospective fixed-version conv-hls pair retains its root; positive integrated confirmation remains pending.', 'Frozen conv-hls confirmation retains its root; TPU arms time out before a legal root. Fixed-scope robot union ablation isolates release-enabled resource feasibility; positive complete-controller benefits remain pending.')
new=new.replace('Independent complete confirmation and positive integrated branch coverage remain pending.', 'One fixed-version no-op pair is confirmed; positive complete-controller benefits remain pending.')
new=new.replace('Outside-project observation, a known R1 owner transaction and an existing tiny whole flow pass; positive automatic owner reentry, positive integrated timing feedback and independent benefits remain unverified.', 'Outside-project checks pass. Four automatic robot-p1 owner commits/reentries are verified on a partial development trajectory; complete-controller positive timing/owner coverage and independent benefits remain unverified.')
anchor='This confirms one fixed-menu no-op input, without global optimality or interleaved speedup.'
new=new.replace(anchor,anchor+' The same sealed cohort retains TPU N/D initial execution timeouts: 1800-s native limits, 1904.67/1906.23-s complete attempts, no legal roots or paired quality. These are execution-budget outcomes, not 200-iteration congestion failures or infeasibility certificates. Two distinct known inputs yield one legal no-op pair; neither arm is an independent sample.')
start=new.index("In robot's first matched transaction")
end=new.index('\\subsection{Blocking-owner coordination}',start)
new=new[:start]+r'''Robot's original 23-connection release-off transaction fails and restores its source exactly. A source-cut audit proves a conditional domain obstruction: outside owners occupy every same-layer exit, while the retained domain lacks a return crossing. Release enables search but does not remove those owners.

A new matched union holds the 25-connection/five-net scope fixed across unrestricted, domain/no-release and domain/release arms. No-release rolls back. Release yields 251160 wire/9 SB/653 CB at unchanged 13.354624073 ns, versus root 251161/10/653; 240 setup components improve, 32 regress, and hold violations do not increase. It passes the fixed resource-under-timing rule, but fails endpoint nonregression. Unrestricted yields 251140/9/654, improving 240 setup components without regression but exceeding the 653-CB cap. Thus retained domains alter the attainable tradeoff, and selective release restores feasibility within that domain; neither isolates a complete-controller gain. All are imported observations, with no actor commit. The shared command costs 194.52 s; cores are 3.00/1.62/4.45 s, not complete arm times.

'''+new[end:]
anchor='\\subsection{Grouping and complete combinations}'
new=new.replace(anchor,r'''On robot-p1, four automatic unrestricted owner commits reenter the current state under the original root envelope: 231045/47/6677 becomes 231113/47/6673 at unchanged 11.633691344 ns. This trades 68 wire for four CB. One step regresses a setup component; resource acceptance does not require endpoint nonregression. Exact existing reload STA, endpoint identities and constraints match the source; a rounded display/manifest comparison caused a check failure. The trajectory remains incomplete development evidence, not domain attribution or fixed-version confirmation.

'''+anchor)
new=new.replace('Twelve later complete attempts, nine infrastructure failures and two scoped components are outside those counts.', 'Fourteen later terminal attempts, nine infrastructure failures and five scoped components are outside those counts.')
new=new.replace('Domain/release need separate ablations.', 'The robot union separates domain/release at one fixed scope; cross-input confirmation remains necessary.')
new=new.replace('Crossing redundancy enables sharing; capacity obstruction justifies an owner proposal; current slack screens complete cuts.', 'Crossing redundancy enables sharing; capacity obstruction plus a useful relaxed witness motivates owner expansion; current slack screens complete cuts. This selection rule is a development hypothesis, not a confirmed universal classifier.')
# Keep the main text centered on mechanisms; detailed historical trajectories remain supplementary.
new=new.replace('A current-margin selector adds one blocking-owner branch to the target\'s four connections.', 'A current-margin selector adds one owner branch.')
source=p/'current_repair_cohort_mechanism_15.tex';source.write_text(new)
files=[Path(__file__).resolve(),parent_path,cohort_path,union_path,owner_path,source]
for src in [cohort_path,union_path,owner_path]:
    dest=e/src.parent.name/src.name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
write(e/'outcomes.json',dict(passed=True,cohort=dict(registered_inputs=2,roles=4,legal_roles=2,legal_matched_inputs=1,initial_timeouts=2),
    union=summary,shared_imported_seconds=u['complete_imported_three_arm_seconds'],
    shared_sampled_PSS_kib=u['measurement']['sampled_tree_PSS_peak_kib'],missing_memory_observations=3,
    owner_reentry=dict(verified_commits=4,full_method_complete=False,exact_existing_reload_identity=True),
    new_independent_physical_inputs=0,newly_closed_confirmed_cohort_inputs=2,new_native_calls=0))
write(e/'edit_registration.json',dict(parent=str(parent_path),source=str(source),
    original_table_rows=38,main_table_rows=43,terminal_attempt_rows=36,infrastructure_grouped_rows=2,scoped_rows=5,
    added_rows=rows+union_rows,source_sha256={str(f):sha(f) for f in files}))
print(dict(source=str(source),main_rows=43,terminal_attempts=36,scoped_rows=5))
