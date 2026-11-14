#!/usr/bin/env python3
"""Preserve attempt01; record only guide-bearing searches before applying row cap."""
import difflib
from retained_prefix_workflow import D,read,write,sha
parent=read(D/'current_eligibility_stage_01/binding.json');assert all(sha(D/'src'/p)==h for p,h in parent['source_sha256'].items())
out=D/'current_eligibility_implementation_02';out.mkdir(exist_ok=False)
p=D/'src/vpr/src/route/h3d_routing.cpp';before=p.read_text();(out/p.name).write_text(before)
a='    if (!settings().current_guide_eligibility) return true;\n    VTR_ASSERT(influence);'
assert before.count(a)==1
s=before.replace(a,'    if (!settings().current_guide_eligibility || !guide) return true;\n    VTR_ASSERT(influence);',1);p.write_text(s)
write(out/'binding.json',dict(status='implemented_not_built',parent='current_eligibility_stage_01',source_binding={p.name:dict(before_sha256=sha(out/p.name),after_sha256=sha(p))},script_sha256=sha(__file__),qualification='Diagnostic-only correction: null guide was never suppressed; early return prevents irrelevant searches exhausting row cap. All guided decisions/counters retained; compare corrected native runs to prior same settings after filtering new eligibility records.'))
(out/'implementation.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),s.splitlines(True),fromfile='a/'+p.name,tofile='b/'+p.name)))
write(D/'current_eligibility_trace_recovery_01.json',dict(status='registered_before_recovery',problem='Attempt01 logs all setup searches but domain observer logs only guides/focus; first20000 irrelevant searches consume eligibility trace cap. Final cumulative decision counts and QoR remain valid, complete mechanism audit not passed.',action='Return true without logging when no guide (already guaranteed eligible). Same algorithm/configuration, new immutable stage02, C2/E2/E1 full same-setting records/physical routes/guide reproduction against original attempt plus complete guided-only eligibility audit.',route_calls=3,qualification='Diagnostic recovery only; neither independent scientific repetitions nor additional circuits. Preserve all attempt01 outputs.'))
base=(D/'prepare_current_eligibility.py').read_text().replace('current_eligibility_stage_01','current_eligibility_stage_02').replace('current_eligibility_implementation_01','current_eligibility_implementation_02').replace('prepare_current_eligibility.py','prepare_current_eligibility_v2.py')
(D/'prepare_current_eligibility_v2.py').write_text(base)
