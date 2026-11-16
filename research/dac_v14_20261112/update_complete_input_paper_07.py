"""Integrate complete BNN cost and both new input outcomes without changing policies."""
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

p = D/'paper'
parent_path = D/'native_ablation_paper_binding_06.json'
parent = read(parent_path)
old = (p/'current_repair_main.tex').read_text()
assert old == (Path(parent['snapshot'])/'current_repair_main.tex').read_text()
e = D/'complete_input_paper_evidence_07'
assert read(e/'completion.json')['passed']
rows = read(e/'rows.json')
new = old
def replace(a,b):
    global new
    assert new.count(a) == 1, a
    new = new.replace(a,b)

replace('Robot transfer saves one CB for 20 wire; both conv-layer roles fail initial routing.',
    'Robot transfer saves one CB for 20 wire; a distinct constrained robot input has no applicable sharing cut or accepted timing repair. Conv-layer and attention pairs fail initial routing.')
replace('The complete serial development controller is independently packaged; actual execution checks and new-circuit/explicit-SDC pairs are queued.',
    'An independently packaged native observer reproduces FULL/STA, endpoints and physical checks outside the project. Nonempty transaction and whole-controller execution checks remain pending; the completed explicit-SDC pair below uses the earlier integration version.')
replace('Router seed 11; SB 102\\% fixes CPD at 1.02 times the root.',
    'Router seed 11; Robot SDC uses different actual placement and 20-ns clock/1-ns maximum I/O constraints. SB 102\\% fixes CPD at 1.02 times the root.')
anchor = '\\multicolumn{6}{l}{Fixed imported-scope components (not complete configurations)}\\\\'
lines=[]
for row in rows:
    if row['resources'] is None:
        lines.append(f"{row['label']}&--&--&{row['time_seconds']:.2f}&--&--\\\\")
    else:
        r=row['resources']; d=row['endpoint_summary']
        lines.append(f"{row['label']}&{row['CPD_ns']:.6f}&{r['wirelength']}/{r['SB_pairs']}/{r['CB_sources']}&{row['time_seconds']:.2f}&{row['PSS_GiB']:.3f}&{d['setup_improved']}/{d['setup_regressed']}/{d['hold_violation_regressions']}\\\\")
replace(anchor, '\n'.join(lines)+'\\hline\n'+anchor)
replace('The first 22 rows of Table~\\ref{tab:completecost} bind complete times to their own outputs; the last two are fixed-scope components.',
    'The first 27 rows of Table~\\ref{tab:completecost} report complete attempts, including four initial failures; the last two are scoped components.')
anchor='On the fixed eltwise packing/placement,'
newpara=('The new robot input changes actual placement and supplies an explicit 20-ns clock with maximum/minimum I/O delays of 1/0 ns. '
    'Both arms have identical initial route bodies/full vectors and identical final vectors: 12.727250365 ns,250411 wire,2 SB,526 CB. '
    'All 10972 observed setup and hold components are finite and nonnegative. This is a declared benchmark target, not an external application requirement. '
    'Neither sharing nor owner screening finds an eligible cut; all three timing proposals are rejected. A legal 12.671110383-ns proposal spends eight wire,one SB and one CB beyond the registered resource limits. '
    'The fixed rule retains the root at 498.00/504.09 s (descriptive +1.22\\%); no mechanism benefit is established. '
    'Attention fails initial routing in both arms after 200 iterations with 231 overused nodes, costing 794.67/792.69 s; repair is never entered. '
    'These four development roles yield two legal outputs on one known physical input, not two independent successes.\n\n')
assert new.count(anchor)==1
new=new.replace(anchor,newpara+anchor)
replace('The same two rules find no replacement in the two robot menus. ', '')
replace('A preregistered three-net composition now passes native FULL/STA and independent physical checks: 2059607 wire,82 SB,5062 CB at 13.228145690 ns, saving 24 wire from its source. Two setup components improve without regression; all 34 predicted connection delays match exactly. Its 217.95 s is imported-candidate validation, not a complete flow or an independent input.',
    'The three-net composition passes native FULL/STA: 2059607 wire,82 SB,5062 CB at 13.228145690 ns, saving 24 wire from its source with two setup improvements and no regression; all 34 predicted delays match. Its 217.95 s covers imported validation. A separate complete terminal-selection flow reaches the same scalar quality in 7351.26 s, including fresh routing, indexes, rejected proposals and three timing commits. It is the same BNN input; baseline-prefix and final-vector attribution require their separate audit, not scalar coincidence.')
replace('Resource-prefix combinations also expose wire/vertical tradeoffs, but exclude upstream routing and preparation costs; those local trajectories remain in the supplement.\n\n','')
replace('A two-connection intervention produces 2070657 wire at the same vertical counts and full vector in both native arms and a separate BFS construction. It is legal but dominated by the five-connection result. Fewer queries did not reduce the measured core time. Detailed paths, core timings and audits remain in the supplement; shared diagnostic costs are not complete-flow measurements.',
    'A two-connection alternative spends four more wire at the same vertical counts/vector and is dominated by the five-connection result. Its smaller query count does not reduce measured core time; paths and scoped costs remain in the supplement.')
replace('Batch grouping is not a reliable cost proxy. K 8 and budget64 execute the same 2722-query multiset in 18 versus 32 transactions, taking 7099.32/10568.53 s. A completed factor-two proposed-query heuristic takes 10308.49 s at the same CPD/SB/CB as K 8. These historical imported observations do not show a cost benefit or statistical speedup; detailed trajectories remain in the supplement.',
    'Batch grouping is not a reliable cost proxy. K 8 and budget64 execute the same query multiset in 18/32 transactions at 7099.32/10568.53 s; a proposed-query heuristic takes 10308.49 s at the same CPD/SB/CB. These historical imported observations show no cost benefit.')
replace('The two new scoped table rows are outside those archive counts; failed transactions have no candidate quality. Initial failures remain inside cohort denominators.',
    'The five new complete attempts and two scoped rows are outside those historical counts. Failed routes/transactions carry no legal quality. The new BNN and robot N/D PSS samples miss 24 and 5/2 observations, respectively; sampling peaks are not exact maxima.')
replace('Flat routing, CHANZ, general multilayer devices, altered placements and broad timing-constrained application suites remain unconfirmed.',
    'Flat routing, CHANZ, general multilayer devices and broad timing-constrained application suites remain unconfirmed. One altered robot placement with declared SDC adds a no-gain case, not broad placement robustness.')
replace('Since BNN currently uses default constraints, application timing claims additionally require new paired instances with explicit SDC clocks and I/O requirements~\\cite{vprsdc}; a development-relative CPD cap is not such a requirement.',
    'BNN uses defaults; the robot SDC benchmark supplies explicit clock/I/O constraints~\\cite{vprsdc}, but external application timing claims still require corresponding application requirements. A relative CPD cap is not such a requirement.')
source = p/'current_repair_complete_inputs_07.tex'
transaction_check = D/'standalone_transaction_native_check_01/completion.json'
if transaction_check.exists() and read(transaction_check)['passed']:
    replace('Nonempty transaction and whole-controller execution checks remain pending; the completed explicit-SDC pair below uses the earlier integration version.',
        'A known R1 owner transaction also reproduces its request, route body, full endpoints, physical audit and acceptance outside the project. Whole-controller confirmation remains pending; the explicit-SDC pair below uses the earlier integration version.')
assert not source.exists()
source.write_text(new)
write(e/'edit_registration.json', dict(parent=str(parent_path), source=str(source),
    complete_attempt_rows=27, scoped_component_rows=2, initial_failure_rows=4,
    sources_sha256={str(f):sha(f) for f in [Path(__file__).resolve(), parent_path, source, e/'completion.json',e/'rows.json',
      D/'unified_input_integration_01/plan.json',D/'standalone_native_observation_equivalence_01/completion.json']},
    qualification='Retain six-section structure and existing mechanisms. Own-output costs and own-root endpoints. Known inputs, no frozen confirmation or statistical speedup.'))
print(dict(source=str(source), complete_rows=27, scoped_rows=2))
