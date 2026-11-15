"""Integrate the completed engineering control without fabricating observer cost fields."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from endpoint_timing_policy_streaming_v2 import compare
paper=D/'paper';source=paper/'current_repair_unified_engineering_02.tex';assert not source.exists()
proof=D/'orphaned_BNN_quality_analysis_02/completion.json';quality=read(proof)
cost=D/'orphaned_BNN_engineering_comparison_01/completion.json';engineering=read(cost)
assert quality['passed'] and engineering['passed'] and engineering['all_actual_work_comparisons_exact']
vectors=[Path(quality[k])/'endpoint_vector.json' for k in ['initial_state','final_state']]
delta=compare(*map(read,vectors));assert delta['compatible']
rows=read(D/'unified_main_table_evidence_01/rows.json')
row=dict(label='BNN stream N',case=str(D/'complete_BNN_closed_stream_flow_01/bnn_native_closed_stream'),
    quality=dict(CPD_ns=quality['CPD_ns'],**quality['resources']),complete_seconds=engineering['GNU_time_elapsed_seconds'],
    time_scope='original full-command GNU-time elapsed; one-second display resolution; observer lost and brief overlap',
    time_tex='7247$^{*}$',memory=dict(sampled_tree_PSS_peak_kib=None,waited_process_RSS_high_water_kib=quality['waited_process_RSS_high_water_kib']),
    endpoint_reference='same configuration initial legal route',endpoint_comparison=delta,source=str(proof),cost_source=str(cost),
    original_complete_observer_measurement_available=False)
index=next(i for i,r in enumerate(rows) if r['label']=='BNN index N')+1;rows.insert(index,row)
text=(paper/'current_repair_main.tex').read_text()
marker=next(line for line in text.splitlines() if line.startswith('BNN index N&'))
line='BNN stream N&13.228146&2059631/82/5062&7247$^{*}$&--&'+ '/'.join(str(delta[k]) for k in ['setup_improved','setup_regressed','hold_violation_regressions'])+r'\\'
text=text.replace(marker,marker+'\n'+line)
text=text.replace("not between final arms.}","not between final arms. $^{*}$Original GNU-time, 1-s precision; observer lost, brief overlap, no complete PSS.}",1)
old='The BNN single-pass-index configuration preserves all graph payloads, downstream actual states, requests, native work and final quality. Its whole time is 7463.17 s versus 7933.25 s, a 470.07 s (5.93\\%) descriptive reduction. This is a single native-arm observation; it does not revise the original matched-pair 22.95\\% domain overhead. The same engineering optimization must be applied to both arms before a new comparison.'
new='Single-pass indexing preserves all BNN graph payloads, downstream states, requests, native work and quality at 7463.17 versus 7933.25 s. Explicit same-flow metadata plus streaming parsing also preserves that actual execution. Its original GNU-time records 7247 s (integer-second precision), versus 7463/7933 s in the same clock scope: about 216/686 s less. The observer was lost and another case briefly overlapped; complete PSS is unavailable. This qualified engineering observation neither establishes statistical acceleration nor revises the matched-pair 22.95\\% domain overhead. Both arms need the same stable implementation and interleaved measurement.'
assert old in text;text=text.replace(old,new)
old='The current 658-record archive includes 33 successful modern complete configurations on five known successful circuits and three vertical families. These are configurations, not independent samples. The inherited scalar omitted four early complete configurations; corrected counts are 30 for the 640-record historical archive and 33 for 658. Per-state quality and time are unchanged. Failed initial routes are retained outside legal-quality counts and inside their registered cohort denominators.'
new='The frozen 658-record archive includes 33 successful modern complete configurations on five known successful circuits and three vertical families; these are not independent samples. The newly verified streaming control is listed separately in the main table, pending archive incorporation. Historical count corrections remain in the supplement. Initial failures remain outside legal-quality counts and inside their cohort denominators.'
assert old in text;text=text.replace(old,new)
text=text.replace('The automatic ordering and interaction of the mechanisms must be fixed before a confirmation cohort.','The development entry implements this ordering; attention and a distinct robot placement with explicit SDC are registered. Complete frozen-controller confirmation remains pending.')
source.write_text(text)
out=D/'unified_main_table_evidence_02';out.mkdir(exist_ok=False);write(out/'rows.json',rows)
files=[Path(__file__).resolve(),proof,cost,*vectors,D/'unified_main_table_evidence_01/completion.json',D/'unified_main_table_evidence_01/rows.json']
write(out/'completion.json',dict(passed=True,rows=22,legal_rows=20,failed_initial_rows=2,original_observer_missing_rows=1,
    new_independent_inputs=0,source_sha256={str(f):sha(f) for f in files},artifact_sha256={'rows.json':sha(out/'rows.json')},
    qualification='One actual full quality engineering control added with original GNU-time elapsed explicitly distinguished from complete observer wall/PSS; existing 21 rows retained. Archive658 count unchanged pending incorporation.'))
print(dict(passed=True,rows=22,source=str(source),new_endpoint_changes={k:delta[k] for k in ['setup_improved','setup_regressed','hold_violation_regressions']}))
