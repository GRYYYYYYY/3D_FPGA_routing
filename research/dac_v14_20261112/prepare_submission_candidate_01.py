"""Create an independent evidence-closed submission candidate from paper19."""
import re,shutil
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

parent=D/'paper_snapshots/current_balanced_cost_20261116'
out=D/'submission_candidate_01';assert not out.exists()
binding=read(D/'balanced_cost_paper_binding_19.json')
assert binding['passed'] and all(sha(p)==h for p,h in binding['source_sha256'].items())
source=parent/'current_repair_main.tex';text=source.read_text();changes=[]
def replace(old,new):
    global text
    assert text.count(old)==1,old
    text=text.replace(old,new);changes.append([old,new])
replace('Anonymous development manuscript','Anonymous submission')
replace('A prospective frozen conv-hls pair confirms a no-op, not positive controller benefit. Symmetric engineering and complete costs remain essential to assessing these tradeoffs.',
        'A prospective frozen conv-hls pair confirms a no-op. The evidence establishes conditional resource--timing tradeoffs and scoped mechanism effects, with complete cost and endpoint regressions determining their engineering value.')
replace('The contributions supported here are matched local mechanism effects, complete resource/time tradeoffs and explicit failure/applicability accounting. The fully integrated frozen controller remains a confirmation target.',
        'We contribute a transactional formulation that separates scope construction, whole-candidate acceptance and terminal selection; matched experiments distinguishing domain restriction, failure release and owner coordination; and complete resource/time tradeoffs with explicit negative outcomes. Claims apply to the configurations and scopes tested, without assuming that combining all mechanisms improves every input.')
replace('These design parameters do not define research termination.','These envelopes are fixed before each trajectory and remain unchanged after commits.')
replace('One fixed-version no-op pair is confirmed; positive complete-controller benefits remain pending. A mechanism branch is not assumed to improve every metric.',
        'Complete-flow results and fixed-scope ablations test different aspects of this contract. Each branch is evaluated under its stated envelope; no branch is assumed to improve every metric.')
replace('These are development triggers, not validated benefit predictors.',
        'These conditions generate proposals; whole-candidate checks determine whether a proposal improves the selected objectives.')
replace('Four automatic robot-p1 owner commits/reentries are verified only on a partial development path; positive complete-controller benefits remain unconfirmed. Development runs are not retroactively confirmation.',
        'Complete-flow observations and prospective fixed-version confirmation are labeled separately; the latter includes a legal no-op and initial timeouts.')
partial=next(p for p in text.split('\n\n') if p.startswith('On robot-p1, four automatic unrestricted owner commits'))
replace(partial,'The complete R1 and fixed-scope robot controls establish the attribution boundary: enlarging coordination scope can change the tradeoff, but a capacity witness alone guarantees neither resource savings nor acceptance. Interrupted owner trajectories and their recovery audits are supplementary provenance records.')
replace('Corrected CLSTM N/D, robot-p1 N and reduction N/D reach legal initial routes before supervision interruption. Four CP1r1 attempts fail guard launch before VPR. Original failures/costs remain. CP1r2 fixes runtime supervision and permissions; actual guard tests/public reconstruction pass without algorithm changes.',
        'Supervision interruptions and pre-VPR guard-launch errors are infrastructure outcomes: their spent costs remain in Table~\\ref{tab:completecost}, with no quality attached. CP1r2 corrects supervision and permissions without algorithm changes. Execution termination, independent verification, legal no-gain, routing failure and timeout are distinct outcomes; a successful command alone does not admit quality.')
replace('The robot union separates domain/release at one fixed scope; cross-input confirmation remains necessary.',
        'The robot union separates domain/release at one fixed scope; this counterfactual does not establish a universal full-controller effect.')
replace('The evidence supports specific complete-flow tradeoffs and local mechanisms, not broad controller superiority, timing-closure guarantees or statistical acceleration.',
        '\\subsection{Conclusions}\nCurrent-STA transactional repair exposes useful, conditional timing--resource tradeoffs on fixed 3D routing graphs. The matched BNN flows exchange 1786 wire for 39 SB and two CB at equal CPD, with 24.91\\% mean complete-time overhead in symmetric repeats; setup regressions make the endpoint cost explicit. Fixed-scope controls attribute R1 improvements to coordination and distinguish robot domain restrictions from failure release. No-cut, no-gain, routing-failure and timeout inputs define the measured applicability boundary. These results support selecting mechanisms and terminal policies according to resource scarcity and timing requirements; they do not establish broad controller superiority, timing-closure guarantees or statistical acceleration.')
assert text[text.index('\\begin{thebibliography}'):]==source.read_text()[source.read_text().index('\\begin{thebibliography}'):]
assert [l for l in text.splitlines() if l.count('&')==5]==[l for l in source.read_text().splitlines() if l.count('&')==5]
out.mkdir();shutil.copytree(parent/'data',out/'data');shutil.copytree(parent/'supplement',out/'supplement')
(out/'main.tex').write_text(text)
(out/'supplement/retained_partial_owner_paragraph.txt').write_text(partial+'\n')
write(out/'edit_registration.json',dict(parent=str(source),parent_sha256=sha(source),changes=changes,
    independent_candidate=True,canonical_paper19_unchanged=True,numerical_table_unchanged=True,
    prior_art_references_unchanged=True,new_experiment_results=0,new_native_or_STA_calls=0,
    paper_closure_requires_research_goal_completion=False,paper_closure_requires_recovery_queue_completion=False,
    fixed_core=['problem_definition','mechanism_structure','prior_art_and_contribution_boundary','BNN_complete_tradeoff','completed_scoped_mechanism_evidence'],
    later_confirmation_edit_scope=['relevant_experiment_rows','applicability','abstract','conclusions'],
    qualification='Evidence-closed submission candidate derived from verified paper19. No future result is assumed. Unfinished trajectories are excluded from benefit claims; original complete failures remain. New negative confirmation narrows the empirical claim rather than replacing the method.'))
print(dict(candidate=str(out),edits=len(changes),table_unchanged=True,paper19_unchanged=True))
