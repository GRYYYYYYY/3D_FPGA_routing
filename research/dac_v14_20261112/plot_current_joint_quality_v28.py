#!/usr/bin/env python3
"""Static matched-physical-input quality projections including all external methods."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from retained_prefix_workflow import D, read, write, sha

archive = D / 'multiobjective_revalidated_native_checkpoints_01'
assert read(archive / 'completion.json')['passed']
points = read(archive / 'points.json')
anchor = next(p for p in points if p['id'] == 'native_extra_opportunity_bnn_01/runs/A0')
population = [p for p in points if p['circuit'] == 'bnn' and p['quality_cohort'] == anchor['quality_cohort']]
actor=D/'fused_resource_development_01/bnn_A0_native_only_K8'
domain_actor=D/'fused_resource_development_01/bnn_A0_feedback_K8'
terminal=read(actor/'completion.json');domain_terminal=read(domain_actor/'completion.json')
assert terminal['passed'] and domain_terminal['passed']
assert read(actor/'evaluation_context/input_seal.json')['passed'] and read(domain_actor/'evaluation_context/input_seal.json')['passed']
data = D / 'paper/data'
pdf = data / 'joint_quality_projection_28.pdf'
assert not pdf.exists()
unique = {}
for p in population:
    unique.setdefault((p['CPD_ns'], p['wirelength'], p['SB_pairs'], p['CB_sources']), p)
selected = [
    ('Strong A0', anchor, 'black', 'D'),
    ('Strong R1', next(p for p in points if p['id']=='native_extra_opportunity_bnn_01/runs/R1'), '#4d4d4d', 's'),
    ('Timing first + native K8', next(p for p in points if p.get('state')==read(D/'strong_A0_native_only_K8_summary_01.json')['final_state']), '#1f77b4', 'o'),
    ('Timing first + guided K8', next(p for p in points if p.get('state')==read(D/'strong_A0_paired_K8_summary_01.json')['final_state']), '#9467bd', '*'),
    ('Full native resource + timing', next(p for p in points if p['arm']=='complete_resource_native_then_current_STA_native'), '#2ca02c', 'P'),
    ('Full guided resource + timing', next(p for p in points if p['arm']=='complete_resource_paired_then_current_STA_native'), '#d62728', '^'),
    ('R1 resource: fixed seeds', next(p for p in points if p.get('actor_final_selected') and p['batch']=='stable_seed_transfer_recovery_01'), '#008b8b', 'X'),
    ('R1 whole-net: rejected', next(p for p in points if p['arm']=='R1_whole_net_whole_net_current_criticality'), '#005f73', '+'),
    ('Owner exchange: vector-rejected', next(p for p in points if p['arm']=='sealed_timing_proposal_05'), '#e377c2', 'h'),
    ('Tf resource (dominated)', next(p for p in points if p.get('actor_final_selected') and p['batch']=='stable_seed_transfer_recovery_02'), '#8c564b', '>'),
    ('Budget64 scope: 47SB', next(p for p in points if p['arm']=='budget64_scope_reuse_on'), '#17becf', 'p'),
    ('47SB local native timing', next(p for p in points if p['arm']=='budget47_native_full462_current_STA' and p['CPD_ns']==13.228145689936355), '#bcbd22', 'd'),
    ('Budget64 local timing end', next(p for p in points if p['arm']=='budget47_guided_budget54_current_STA' and p['CPD_ns']==13.228145689936355), '#00a5bd', '<'),
    ('Independent 45SB feedback', next(p for p in points if p['arm']=='same_source_five_connection_vector_feedback'), '#ff7f0e', 'v'),
]
assert all(p['quality_cohort'] == anchor['quality_cohort'] for _, p, _, _ in selected)
plt.rcParams.update({'font.size': 8, 'axes.labelsize': 8, 'legend.fontsize': 7, 'pdf.fonttype': 42})
fig, grid = plt.subplots(2, 3, figsize=(7.1, 4.7));axes=grid.ravel()
for ax, key, ylabel, scale in zip(axes, ['wirelength', 'SB_pairs', 'CB_sources']*2, ['Planar wire (million units)', 'Actual SB pairs', 'Actual CB output sources']*2, [1e6, 1., 1.]*2):
    cloud = list(unique.values())
    ax.scatter([p['CPD_ns'] for p in cloud], [p[key] / scale for p in cloud], c='#bdbdbd', s=12, alpha=.65, label='All legal quality tuples')
    for label, point, color, marker in selected:
        ax.scatter([point['CPD_ns']], [point[key] / scale], c=color, marker=marker, s=38 if marker != '*' else 64,
                   edgecolors='white', linewidths=.4, label=label, zorder=5)
    if list(axes).index(ax)>=3:
        ax.set_ylim({'wirelength':(2.05948,2.06146),'SB_pairs':(29,108),'CB_sources':(5057,5075)}[key])
        ax.set_title('Low-resource detail',fontsize=8)
    else:ax.set_title('Same physical input',fontsize=8)
    ax.set_xlabel('CPD (ns)')
    ax.set_ylabel(ylabel)
    ax.grid(alpha=.18)
    ax.ticklabel_format(useOffset=False, style='plain', axis='y')
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc='lower center', ncol=3, frameon=False, bbox_to_anchor=(.5, -.005))
fig.tight_layout(rect=(0, .16, 1, 1), w_pad=1.5,h_pad=1.2)
fig.savefig(pdf, bbox_inches='tight')
fig.savefig(data / 'joint_quality_projection_28.png', dpi=180, bbox_inches='tight')
plt.close(fig)
fields = ['id', 'arm', 'batch', 'convergence', 'opportunity', 'CPD_ns', 'wirelength', 'SB_pairs', 'CB_sources']
with (data / 'joint_quality_projection_28.csv').open('w') as stream:
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows({k: p[k] for k in fields} for p in population)
write(data / 'joint_quality_projection_binding_28.json', dict(passed=True, archive=str(archive),
    physical_quality_cohort=anchor['quality_cohort'], observations=len(population), unique_quality_tuples=len(unique),
    selected_records={name: p['id'] for name, p, _, _ in selected},
    source_sha256={str(p): sha(p) for p in [Path(__file__).resolve(), archive / 'completion.json', archive / 'points.json',actor/'completion.json',actor/'attempts.json',actor/'evaluation_context/input_seal.json',domain_actor/'completion.json',domain_actor/'evaluation_context/input_seal.json',D/'low_resource_timing_accept_03.json']},
    artifact_sha256={n: sha(data / n) for n in ['joint_quality_projection_28.pdf', 'joint_quality_projection_28.png', 'joint_quality_projection_28.csv']},
    qualification='Legal observations from archive541 on identical BNN physical inputs, including strong A0/R1/U/Tf, all sealed extended resource trajectories, seed diagnostics complete-resource timing, independent45SB feedback, all52legal candidates from the six completed fixed-seed resource roles, and three sealed intermediate current-STA commits from the local47SB native alternative. Both47SB local timing menus are terminal. The budget64 guided54-connection-source final dominates the local native final in four quality coordinates, but this is not a whole pristine-native trajectory, isolated domain/grouping causal claim or complete fresh-route algorithm-cost comparison. The completed43SB resource/timing chain and independent45SB feedback retain distinct inputs/opportunities. Historical pilot points are not universal native bounds. Two completed whole-net R1 candidates save20wire with unchanged endpoint vector and33SB/5071CB; original vertical-only policy rejects, no actor commit. Seed19 complete configurations reproduce seed11 roots/trajectories and add no independent samples. Four separately sealed native-checkpoint/pending LOAD observations added: all dominated, none a closed native trajectory or committed new transition. Physical audit reuse for exact checkpoint bytes is explicit; pending candidates have actual new independent audits. No two-dimensional/full-time Pareto boundary, whole configuration speedup or per-circuit history-best policy inferred; versions/convergence remain explicit in CSV. Fixed-device occupancy is not area/power.'))
print(dict(population=len(population), unique=len(unique), pdf=str(pdf)), flush=True)
