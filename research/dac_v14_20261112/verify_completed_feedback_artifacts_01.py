"""Read-only replay of the current archive, manuscript and snapshot bindings."""
from pathlib import Path
from pypdf import PdfReader
from retained_prefix_workflow import D,read,sha

archive=D/'multiobjective_completed_feedback_01'
receipt=read(archive/'completion.json');assert receipt['passed'] and receipt['records']==336
for n,h in receipt['artifact_sha256'].items():assert sha(archive/n)==h,n
for p,h in receipt['source_sha256'].items():assert sha(p)==h,p
binding=read(D/'completed_feedback_paper_binding_01.json');assert binding['passed'] and binding['pages']==6
for p,h in binding['source_sha256'].items():assert sha(p)==h,p
snapshot=Path(binding['snapshot']);sealed=read(snapshot/'snapshot_binding.json')
for n,h in sealed['files'].items():assert sha(snapshot/n)==h,n
assert sha(D/'paper/current_repair_main.tex')==sha(snapshot/'current_repair_main.tex')
assert len(PdfReader(binding['pdf']).pages)==6
points=read(archive/'points.json')
arms=['complete_resource_native_then_current_STA_native','complete_resource_paired_then_current_STA_native','same_source_five_connection_vector_feedback']
native,paired,feedback=[next(p for p in points if p['arm']==arm) for arm in arms]
assert native['CPD_ns']==paired['CPD_ns']==13.228145689936355
assert [paired[k]-native[k] for k in ['wirelength','SB_pairs','CB_sources']]==[1762,-39,-2]
assert all(p['quality_status']=='nondominated_in_collected_population' for p in [native,paired,feedback])
assert all(p['complete_single_configuration_seconds'] is None for p in [native,paired,feedback])
summary=read(archive/'composition_summary.json')
delta=summary['feedback_endpoint_comparison']
assert delta['setup_improved']==10 and delta['setup_regressed']==0 and delta['hold_violation_regressions']==0
assert summary['paired_43SB_timing_trajectory_terminal']
print(dict(passed=True,archive_records=len(points),paper_pages=6,source_pdf_snapshot_consistent=True,native_calls=0),flush=True)
