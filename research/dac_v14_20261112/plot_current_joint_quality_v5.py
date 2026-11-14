#!/usr/bin/env python3
"""Static matched-physical-input quality projections including all external methods."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from retained_prefix_workflow import D, read, write, sha

archive = D / 'multiobjective_archive_52'
assert read(archive / 'completion.json')['passed']
points = read(archive / 'points.json')
anchor = next(p for p in points if p['id'] == 'native_extra_opportunity_bnn_01/runs/A0')
population = [p for p in points if p['circuit'] == 'bnn' and p['quality_cohort'] == anchor['quality_cohort']]
actor=D/'fused_resource_development_01/bnn_A0_native_only_K8'
terminal=read(actor/'completion.json')
assert terminal['passed'] and read(actor/'evaluation_context/input_seal.json')['passed']
observations=[actor/'initial']
for attempt in read(actor/'attempts.json'):
    observations.extend(Path(row['evaluation']) for row in attempt['pair'].values() if row.get('status')=='legal_evaluated')
for state in observations:
    c=read(state/'completion.json');assert c['passed']
    rd=Path(c['run']);m=read(rd/'manifest.json');a=read(rd/'independent_audit.json');assert a['audit']['passed'] and m['metrics']['native_full_check_passed']
    graph=m['command'][m['command'].index('--read_rr_graph')+1]
    assert m['shared_inputs'][graph]['sha256']==anchor['physical_identity']['graph']
    assert m['private_input_sha256'][str(rd/'packed.net')]==anchor['physical_identity']['packed'] and m['private_input_sha256'][str(rd/'placed.place')]==anchor['physical_identity']['placed']
    ident=str(rd.relative_to(D))
    if not any(point['id']==ident for point in population):
        metrics=a['physical_metrics'];vector=read(state/'endpoint_vector.json')
        point=dict(anchor,id=ident,arm='extended_native_A0',state=str(state),batch='fused_resource_development_01/bnn_A0_native_only_K8',
            convergence='own_current_native_menu_exhaustion',opportunity='Pristine strongA0 fixed seed-native K8/rank3 trajectory with no2commit cap; final context seal passed',
            CPD_ns=vector['cpd_s']*1e9,wirelength=metrics['planar_wirelength_excluding_sb_half_nodes'],SB_pairs=metrics['sb_pairs_used'],CB_sources=metrics['cb_crossing_output_sources_used'])
        population.append(point);points.append(point)

data = D / 'paper/data'
pdf = data / 'joint_quality_projection_05.pdf'
assert not pdf.exists()
unique = {}
for p in population:
    unique.setdefault((p['CPD_ns'], p['wirelength'], p['SB_pairs'], p['CB_sources']), p)
selected = [
    ('Strong A0', anchor, 'black', 'D'),
    ('Strong R1', next(p for p in points if p['id'] == 'native_extra_opportunity_bnn_01/runs/R1'), '#4d4d4d', 's'),
    ('A0 fast + native K8', next(p for p in points if p.get('state') == read(D / 'strong_A0_native_only_K8_summary_01.json')['final_state']), '#1f77b4', 'o'),
    ('A0 fast + guided K8', next(p for p in points if p.get('state') == read(D / 'strong_A0_paired_K8_summary_01.json')['final_state']), '#d62728', '^'),
    ('R1 selective release', next(p for p in points if p.get('state') == read(D / 'failure_feedback_domain_dev_02/completion.json')['final_state']), '#9467bd', '*'),
    ('Pristine A0/native K8', next(p for p in points if p.get('state') == read(D / 'uniform_feedback_resource_dev_01/bnn_A0_native_only_K8/completion.json')['final_state']), '#2ca02c', 'P'),
]
selected.append(('Pristine A0/guided K8',next(p for p in points if p.get('state')==read(D/'uniform_feedback_resource_dev_01/bnn_A0_feedback_K8/completion.json')['final_state']),'#17becf','v'))
selected.append(('Extended native A0',next(point for point in population if point.get('state')==terminal['final_state']),'#e377c2','X'))
assert all(p['quality_cohort'] == anchor['quality_cohort'] for _, p, _, _ in selected)
plt.rcParams.update({'font.size': 8, 'axes.labelsize': 8, 'legend.fontsize': 7, 'pdf.fonttype': 42})
fig, grid = plt.subplots(2, 3, figsize=(7.1, 4.5));axes=grid.ravel()
for ax, key, ylabel, scale in zip(axes, ['wirelength', 'SB_pairs', 'CB_sources']*2, ['Planar wire (million units)', 'Actual SB pairs', 'Actual CB output sources']*2, [1e6, 1., 1.]*2):
    cloud = list(unique.values())
    ax.scatter([p['CPD_ns'] for p in cloud], [p[key] / scale for p in cloud], c='#bdbdbd', s=12, alpha=.65, label='All legal quality tuples')
    for label, point, color, marker in selected:
        ax.scatter([point['CPD_ns']], [point[key] / scale], c=color, marker=marker, s=38 if marker != '*' else 64,
                   edgecolors='white', linewidths=.4, label=label, zorder=5)
    if list(axes).index(ax)>=3:
        ax.set_ylim({'wirelength':(2.05948,2.06003),'SB_pairs':(68,108),'CB_sources':(5057,5075)}[key])
        ax.set_title('Low-resource detail',fontsize=8)
    else:ax.set_title('Full matched population',fontsize=8)
    ax.set_xlabel('CPD (ns)')
    ax.set_ylabel(ylabel)
    ax.grid(alpha=.18)
    ax.ticklabel_format(useOffset=False, style='plain', axis='y')
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', ncol=3, frameon=False, bbox_to_anchor=(.5, -.005))
fig.tight_layout(rect=(0, .16, 1, 1), w_pad=1.5,h_pad=1.2)
fig.savefig(pdf, bbox_inches='tight')
fig.savefig(data / 'joint_quality_projection_05.png', dpi=180, bbox_inches='tight')
plt.close(fig)
fields = ['id', 'arm', 'batch', 'convergence', 'opportunity', 'CPD_ns', 'wirelength', 'SB_pairs', 'CB_sources']
with (data / 'joint_quality_projection_05.csv').open('w') as stream:
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows({k: p[k] for k in fields} for p in population)
write(data / 'joint_quality_projection_binding_05.json', dict(passed=True, archive=str(archive),
    physical_quality_cohort=anchor['quality_cohort'], observations=len(population), unique_quality_tuples=len(unique),
    selected_records={name: p['id'] for name, p, _, _ in selected},
    source_sha256={str(p): sha(p) for p in [Path(__file__).resolve(), archive / 'completion.json', archive / 'points.json',actor/'completion.json',actor/'attempts.json',actor/'evaluation_context/input_seal.json',D/'BNN_extended_native_menu_01.json']},
    artifact_sha256={n: sha(data / n) for n in ['joint_quality_projection_05.pdf', 'joint_quality_projection_05.png', 'joint_quality_projection_05.csv']},
    qualification='Projections of the explicit archive52 snapshot plus all9sealed extended native actor observations, including strong A0/R1/U/Tf and repairs. Ongoing paired private states are excluded until their final seal; this is not a claim to an already merged complete-cohort population. No two-dimensional Pareto boundary is asserted because other resources/runtime are hidden. Roots/convergence/opportunities remain explicit in CSV; observed history is not a frozen per-circuit algorithm score. Comparable complete algorithm runtime unknown; fixed-architecture occupancy is not area or power.'))
print(dict(population=len(population), unique=len(unique), pdf=str(pdf)), flush=True)
