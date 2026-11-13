#!/usr/bin/env python3
"""Bounded manuscript verification, not a full experiment acceptance audit."""
from pathlib import Path
from collections import Counter
import csv, datetime, hashlib, json, math, re, statistics
from pypdf import PdfReader
P=Path(__file__).resolve().parent
ROOT=P.parents[1]
s=json.loads((P/'data/evidence_snapshot.json').read_text())
checks=[]
def check(name,ok,detail=None):
    checks.append(dict(name=name,passed=bool(ok),detail=detail))
for path,digest in s['source_sha256'].items():
    check('binding:'+path,hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest)
for panel in s['panels']:
    key=panel['family']+'/'+panel['flow']
    for metric in [panel['dual']['vs_3d'],panel['dual']['vs_2d'],panel['modern']]:
        pc=metric['per_circuit']
        ratios=[x['numerator_mean']/x['denominator_mean'] for x in pc]
        value=100*(1-math.exp(statistics.mean(map(math.log,ratios))))
        check('geomean:'+key,math.isclose(value,metric['geomean_improvement_percent'],abs_tol=1e-9),value)
    m=panel['dual']['vs_3d']
    check('win_tie_loss:'+key,sum(m[x] for x in ['improved_samples','tied_samples','regressed_samples'])==m['paired_legal_samples'])
    for role,c in panel['coverage'].items():check('coverage:'+key+'/'+role,sum(c.values())==42)
for baseline_key,comparison in s['serial']['comparisons'].items():
    baseline=baseline_key.removeprefix('R1_over_')
    for case in comparison['per_case']:
        key=(case['circuit'],case['family'],case['flow'])
        source=next(x for x in s['serial']['cases'] if (x['circuit'],x['family'],x['flow'])==key)
        pairs=[r for r in source['repeats'] if r['routes'][baseline]['status']=='legal' and r['routes']['R1']['status']=='legal']
        check('serial_repeats:'+str(key)+'/'+baseline,len(pairs)==case['paired_legal_repeats'])
        if len(pairs)==3:
            for group,field in [('router','router_seconds'),('route_process','process_wall_seconds')]:
                def val(r,role):
                    obs=r['routes'][role]
                    return obs['metrics'][field] if group=='router' else obs[field]
                ratio=statistics.median(val(r,'R1') for r in pairs)/statistics.median(val(r,baseline) for r in pairs)
                check('serial_ratio:'+str(key)+'/'+baseline+'/'+group,math.isclose(ratio,case[group]['ratio'],abs_tol=1e-12))
for pair in s['mechanisms']:
    for row in pair['pair']:
        check('mechanism_legality:'+row['run'],row['metrics']['native_full_check_passed'] and row['audit']['passed'] and row['pair_check']['passed'])
connections=json.loads((P/'data/connection_changes.json').read_text())
for path,digest in connections['source_sha256'].items():
    check('connection_binding:'+path,hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest)
check('connection_status',connections['status']=='paired_terminals_verified')
for case in connections['cases']:
    check('terminal_identity:'+case['circuit'],case['terminal_identity_equal'])
    for group,row in case['groups'].items():
        key=case['circuit']+'/'+group
        check('connection_counts:'+key,sum(row[k] for k in ['improved','tied','regressed'])==row['count'])
        check('connection_mean_delta:'+key,math.isclose(row['r1_mean_ns']-row['a0_mean_ns'],row['mean_delta_ns'],abs_tol=1e-12))
        for direction in ['largest_improvements','largest_regressions']:
            check('connection_extreme_delta:'+key+'/'+direction,all(math.isclose(x['r1_ns']-x['a0_ns'],x['delta_ns'],abs_tol=1e-12) for x in row[direction]))
closed=json.loads((P/'data/closed_metadata_audit.json').read_text())
check('closed_audit_explicitly_partial',closed['status']=='small_files_and_execution_metadata_verified_large_files_pending')
check('closed_audit_no_reported_issues',not any(closed[k] for k in ['missing','conflicts','mismatches']))
for path,digest in closed['source_maps_sha256'].items():
    check('closed_map_binding:'+path,hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest)
records_path=P/closed['records_file']
check('closed_records_binding',hashlib.sha256(records_path.read_bytes()).hexdigest()==closed['records_sha256'])
records=[json.loads(line) for line in records_path.read_text().splitlines()]
check('closed_records_count',len(records)==closed['unique_inodes'])
check('closed_hashed_count',sum(r['status']=='verified' for r in records)==closed['hashed_unique_files'])
check('closed_deferred_count',sum(r['status']=='deferred_large_file' for r in records)==closed['deferred_unique_files'])
check('closed_recorded_run_checks',len(closed['run_checks'])==1136 and all(r['passed'] for r in closed['run_checks']))
check('training_denominator',sum(r['count'] for r in closed['training_counts'])==594)
check('configuration_frozen_before_heldout',closed['selection_precedes_heldout'] and closed['selection_utc']<closed['first_heldout_route_start_utc'])
B=ROOT/'results/architecture_flow_20261027/serial_strict_reexecution_20261103'
observations=json.loads((B/'evaluation_analysis/role_observations.json').read_text())['rows']
primary=[r for r in observations if r['phase']=='heldout' and r['family']!='matched_2d' and r['role'] in ['A0','R1','B2']]
coverage=Counter('legal' if r['status']=='legal' else r['failure_class'] for r in primary)
check('primary_3d_coverage',len(primary)==756 and coverage==Counter(legal=354,routing_failure=280,process_timeout=121,allocation_failure_under_registered_limit=1),dict(coverage))
unique_runs={r['run']:r for r in observations if r['run']}
check('nonlegal_cpd_is_not_legality',sum(r['status']!='legal' and r.get('metrics',{}).get('critical_path_ns',0)>0 for r in unique_runs.values())==closed['nonlegal_runs_with_positive_logged_cpd']==385)
contracts=json.loads((P/'data/comparison_contract_audit.json').read_text())
contract_mismatches=[path for path,digest in contracts['source_sha256'].items() if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest]
check('comparison_contract_source_bindings',not contract_mismatches,dict(files=len(contracts['source_sha256']),mismatches=contract_mismatches))
check('comparison_contract_recorded_checks',contracts['status']=='passed_with_explicit_scope_limits' and len(contracts['checks'])==987 and all(c['passed'] for c in contracts['checks']))
check('comparison_contract_scope',len(contracts['models'])==10 and contracts['legal_pair_count']==552 and contracts['serial']['process_count']==180 and not contracts['serial']['overlaps'])
toolchain=json.loads((P/'data/toolchain_provenance.json').read_text())
toolchain_mismatches=[path for path,digest in toolchain['source_sha256'].items() if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=digest]
check('toolchain_source_bindings',not toolchain_mismatches,dict(files=len(toolchain['source_sha256']),mismatches=toolchain_mismatches))
check('toolchain_recorded_checks',toolchain['status']=='verified_with_reconstruction_limits' and all(c['passed'] for c in toolchain['checks']))
check('toolchain_roles',{r['role'] for r in toolchain['roles']}=={'A0','R1','B2','P1'})
p1_roundtrip=json.loads((P/'data/p1_patch_roundtrip.json').read_text())
check('p1_exported_patch_binding',p1_roundtrip['passed'] and hashlib.sha256((P/'provenance/placement_p1_serial.patch').read_bytes()).hexdigest()==p1_roundtrip['patch_sha256'])
tex=(P/'main.tex').read_text()
abstract=re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',tex,re.S).group(1).strip().replace('\\%','%')
check('abstract_99_words',len(abstract.split())==99)
check('abstract_file_matches',abstract==(P/'abstract.txt').read_text().strip())
pdf=PdfReader(P/'build/main.pdf')
check('six_body_plus_one_reference_page',len(pdf.pages)==7)
texts=[p.extract_text() for p in pdf.pages]
# IEEE small caps can extract as "C ONCLUSION" depending on font subsets.
compact_texts=[re.sub(r'\s+','',t).lower() for t in texts]
check('references_only_final_page',compact_texts[-1].startswith('references') and 'conclusion' not in compact_texts[-1])
check('conclusion_on_body_page',any('conclusion' in t for t in compact_texts[:6]))
width=json.loads((P/'data/paired_width_snapshot.json').read_text())
for path,digest in width['source_sha256_files'].items():
    check('width_source:'+path,hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest)
check('width_coverage',width['registered_roles']==144 and width['role_status_counts']==dict(legal=125,failed=13,timeout=6))
selected=[x for x in width['interactions'] if x['role']=='selected_R1']
complete=[x for x in selected if x['status']=='complete']
ratios=[x['effect']['interaction_ratio'] for x in complete]
check('width_interaction_coverage',len(selected)==24 and len(complete)==19)
check('width_interaction_directions',(sum(x<1-1e-9 for x in ratios),sum(abs(x-1)<=1e-9 for x in ratios),sum(x>1+1e-9 for x in ratios))==(5,11,3))
check('width_interaction_arithmetic',all(math.isclose(x['effect']['interaction_ratio'],x['effect']['w300_r1_over_a0']/x['effect']['w100_r1_over_a0'],rel_tol=1e-12) for x in complete))
check('width_pending_marker_removed','Pending update in this subsection only.' not in tex)
check('no_overfull_boxes','Overfull' not in (P/'build/main.log').read_text())
check('no_undefined_citations',not re.search(r'(Citation|Reference).*undefined', (P/'build/main.log').read_text()))
check('no_font_substitution','Some font shapes were not available' not in (P/'build/main.log').read_text())
font_checks=[]
for page in pdf.pages:
    for obj in page['/Resources'].get('/Font',{}).values():
        font=obj.get_object()
        descendants=font.get('/DescendantFonts',[font])
        for desc in descendants:
            desc=desc.get_object();fd=desc.get('/FontDescriptor')
            if fd:
                fd=fd.get_object();font_checks.append(any(k in fd for k in ['/FontFile','/FontFile2','/FontFile3']))
            else:font_checks.append(False)
check('all_referenced_fonts_embedded',all(font_checks),len(font_checks))
report=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='passed' if all(c['passed'] for c in checks) else 'failed',checks=checks,pages=len(pdf.pages),body_pages=6,reference_pages=1,abstract_words=len(abstract.split()),scope='Rehash manuscript and supplementary connection source bindings, recompute reported aggregates and timing ratios, reconcile coverage, inspect sample legality receipts and the partial metadata-audit receipt, PDF page structure and embedded fonts. Does not repeat the metadata audit, re-audit all RRGs/routes or constitute final 13-item acceptance.')
report['reviewed_artifacts_sha256']={name:hashlib.sha256((P/name).read_bytes()).hexdigest() for name in ['main.tex','abstract.txt','build/main.pdf','figures/strict_runtime.pdf','data/evidence_snapshot.json','data/connection_changes.json','data/closed_metadata_audit.json','data/comparison_contract_audit.json','data/toolchain_provenance.json','data/p1_patch_roundtrip.json','data/paired_width_snapshot.json','verify_draft.py']}
(P/'build/verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(report['status'],len(checks),'checks;',len(pdf.pages),'pages;',len(abstract.split()),'abstract words')
for c in checks:
    if not c['passed']:print('FAILED',c)
raise SystemExit(0 if report['status']=='passed' else 1)
