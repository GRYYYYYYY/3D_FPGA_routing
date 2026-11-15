"""Actual menu transfer and incompatible-tree tests; zero native calls."""
import copy
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from select_terminal_resource_alternative_v1 import select
from compose_terminal_wire_and_timing_v1 import merge_edges

out=D/'terminal_wire_selector_merge_validation_01'
out.mkdir(exist_ok=False)
files=[Path(__file__).resolve(),D/'select_terminal_resource_alternative_v1.py',D/'compose_terminal_wire_and_timing_v1.py',
       D/'BNN_terminal_wire_alternative_01/completion.json']
bindings={str(f):sha(f) for f in files}
write(out/'registration.json',dict(source_sha256=bindings,native_calls=0,
    question='Does the same terminal rule handle closed menus on other known circuits, including zero-eligible cases, and does the three-way tree merge reject incompatible/detached/dangling branches?'))
roots=[('eltwise_native',D/'complete_serial_resource_measurement_dev_01/flow/repair'),
       ('spmv_domain',D/'complete_serial_lazy_transfer_dev_01/spmv_paired/flow/repair'),
       ('softmax_domain',D/'complete_serial_lazy_transfer_dev_01/softmax_paired/flow/repair'),
       ('SB102_domain',D/'complete_serial_timing_budget_01/sb_domain/flow/repair')]
rows=[]
for label,actor in roots:
    result=select(actor,out/label)
    rows.append(dict(case=label,candidates=result['actual_same_source_candidates'],
        eligible=result['eligible_candidates'],selected=result['selected']))
    print(dict(case=label,candidates=result['actual_same_source_candidates'],eligible=result['eligible_candidates']),flush=True)
base=dict(root=0,sinks={1:3,2:6},edges={1:(0,0,0.),2:(1,0,0.),3:(2,0,0.),4:(0,0,0.),5:(4,0,0.),6:(5,0,0.)})
side=copy.deepcopy(base);side['edges'][7]=(1,0,0.);side['edges'][2]=(7,0,0.)
main=copy.deepcopy(base);main['edges'][8]=(4,0,0.);main['edges'][5]=(8,0,0.)
merged,receipt=merge_edges(base,side,main)
assert receipt['compatible'] and merged['edges'][2][0]==7 and merged['edges'][5][0]==8
agree,receipt=merge_edges(base,side,side)
assert receipt['compatible'] and agree==side
conflict=copy.deepcopy(base);conflict['edges'][8]=(1,0,0.);conflict['edges'][2]=(8,0,0.)
result,receipt=merge_edges(base,side,conflict)
assert result is None and 2 in receipt['conflicting_parent_or_switch_nodes']
guards=[]
for name,modify in [('detached_parent',lambda t:t['edges'].__setitem__(2,(99,0,0.))),
                    ('dangling_branch',lambda t:t['edges'].__setitem__(9,(0,0,0.))),
                    ('cycle',lambda t:t['edges'].__setitem__(1,(2,0,0.)))]:
    altered=copy.deepcopy(base);modify(altered)
    try:merge_edges(base,altered,base)
    except (AssertionError,KeyError,RecursionError) as error:
        guards.append(dict(case=name,rejected=True,exception=type(error).__name__))
    else:raise AssertionError(name)
assert all(sha(f)==h for f,h in bindings.items())
write(out/'actual_menu_results.json',rows);write(out/'merge_guards.json',guards)
write(out/'completion.json',dict(passed=True,native_calls=0,actual_additional_menus=len(rows),
    synthetic_positive_merges=2,synthetic_conflicting_merge_rejected=True,
    detached_dangling_cycle_guards=len(guards),source_sha256=bindings,
    artifact_sha256={n:sha(out/n) for n in ['registration.json','actual_menu_results.json','merge_guards.json']},
    qualification='Actual known-menu reuse/transfer, including absence of eligible alternatives, is not a new independent routing experiment. Synthetic tree tests cover shared child-parent conflicts, identical edits, distinct branches and malformed merged trees. Actual composite route still requires whole occupancy and native FULL/STA/independent physical validation.'))
