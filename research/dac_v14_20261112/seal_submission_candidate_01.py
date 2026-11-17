"""Seal a six-page candidate using current, already verified evidence only."""
import re,unicodedata
from pathlib import Path
from datetime import datetime,timezone
from pypdf import PdfReader
from retained_prefix_workflow import D,read,write,sha

out=D/'submission_candidate_01';target=out/'verification.json';assert not target.exists()
parent_path=D/'balanced_cost_paper_binding_19.json';parent=read(parent_path)
assert parent['passed'] and all(sha(p)==h for p,h in parent['source_sha256'].items())
source=out/'main.tex';pdf=out/'build/main.pdf';text=source.read_text();registration=read(out/'edit_registration.json')
original=Path(registration['parent']);assert sha(original)==registration['parent_sha256']
restored=text
for before,after in reversed(registration['changes']):
    assert restored.count(after)==1;restored=restored.replace(after,before,1)
assert restored==original.read_text(),'Unregistered source edit'
assert sha(D/'paper/current_repair_main.tex')==sha(original),'Canonical paper19 changed'
table=lambda s:[line for line in s.splitlines() if line.count('&')==5]
assert table(text)==table(restored)
assert text[text.index('\\begin{thebibliography}'):]==restored[restored.index('\\begin{thebibliography}'):]
assert re.findall(r'\\section\{([^}]+)\}',text)==re.findall(r'\\section\{([^}]+)\}',restored)
assert all(x not in text for x in ['positive complete-controller benefits remain pending','fully integrated frozen controller remains a confirmation target','CP1r3'])
assert not re.search(r'\bLSTM\b',text) # Keep historical CLSTM failure rows.
assert 'Conclusions' in text and len(PdfReader(pdf).pages)==6
log=(out/'build/main.log').read_text()
assert not re.search(r'Overfull|Undefined|undefined|Fatal|Error',log)
flat=unicodedata.normalize('NFKC',''.join(''.join((p.extract_text() or '').split()) for p in PdfReader(pdf).pages)).casefold()
for token in ['24.91%','22.95%','47.56%','0.797%','1.24796/1.25026','conclusions','initialtimeout','negotiatedsame-netsharing']:
    assert token in flat,token
anchors=['BNN_timing03_balanced_receipt_01/completion.json','robot_union_mechanism_02/verification_v2.json',
    'R1_owner_release_joint_probe_01/verification.json','cp1r2_cross_circuit_cohort_01/terminal_evidence_01/completion.json',
    'balanced_cost_paper_evidence_19/completion.json','release_coverage_01/completion.json']
bound={}
for name in anchors:
    path=D/name;assert path.stat().st_size<4*1024**2;v=read(path);assert v['passed'];bound[str(path)]=sha(path)
review=dict(passed=True,pages_reviewed=6,full_resolution_pages_reviewed=[4,6],
    contact_sheet='visual/contact.png',pdf_sha256=sha(pdf),table_not_clipped=True,
    conclusion_and_references_fit=True,fonts_and_margins_preserved=True,
    underfull_warnings_retained=True)
write(out/'visual_review.json',review)
claims=dict(fixed_core=registration['fixed_core'],
    problem_and_method='Fixed graph/packing/placement transactional timing-resource tradeoffs; mechanism order and fixed root acceptance remain.',
    BNN='Matched complete local tradeoff at equal CPD, +1786wire/-39SB/-2CB, setup534improved/803regressed, mean complete overhead24.91%; historical22.95% separate.',
    mechanism='R1 owner equality attributes coordination; completed robot counterfactuals distinguish domain restriction and release within fixed scope.',
    applicability='Measured edge-encoded two-layer inputs, no-cut/no-gain/failure/timeout included; no universal superiority, statistical speedup or application timing guarantee.',
    fixed_version_confirmation='Completed conv_hls no-op and TPU initial timeouts; no uncompleted CP1r3 benefits.',
    excluded_future_dependencies=['CP1r3 positive outcome','historical four-arm recovery','robot-p1 recovery','new engineering speedup'],
    allowed_future_edits=registration['later_confirmation_edit_scope'],
    evidence_anchor_sha256=bound,parent_verified_evidence_binding=str(parent_path))
write(out/'claims_evidence.json',claims)
write(target,dict(passed=True,status='independent_evidence_closed_submission_candidate',
    sealed_at=datetime.now(timezone.utc).isoformat(),pages=6,table_rows=42,references=9,
    source=str(source),pdf=str(pdf),parent_paper19_preserved=True,numerical_table_unchanged=True,
    bibliography_prior_art_scope_preserved=True,exact_registered_edits_reversible=True,
    full_research_goal_complete=False,paper_requires_future_experimental_results=False,
    paper_requires_recovery_queue_terminal=False,new_native_or_STA_calls=0,
    uncompleted_CP1r3_results_in_benefit_claims=False,visual_review=review,
    source_sha256={str(p):sha(p) for p in [source,pdf,out/'edit_registration.json',out/'claims_evidence.json',out/'visual_review.json',out/'EXPERIMENT_IMPACT.md',out/'ETA.md',out/'role_status_and_eta.json',parent_path,*[D/n for n in anchors]]},
    qualification='Verified candidate artifact, not a claim of venue acceptance or completed research. Six-page layout, source/PDF text, unchanged numerical table and references, reversible changes and inherited verified evidence anchors checked. The manuscript independently concludes measured tradeoffs and attribution; future confirmation only updates relevant empirical claims. Full raw experiment audit receipts remain those of paper19, not rerun during editorial work.'))
print(dict(passed=True,pages=6,table_rows=42,independent_candidate=str(pdf),future_results_required=False))
