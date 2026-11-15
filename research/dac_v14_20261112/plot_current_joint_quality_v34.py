#!/usr/bin/env python3
"""Static matched-physical-input quality projections including all external methods."""
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from retained_prefix_workflow import D, read, write, sha

archive = D / 'multiobjective_connection_budget_closed_01'
assert read(archive / 'completion.json')['passed'] and read(archive/'verification.json')['passed']
points = read(archive / 'points.json')
anchor = next(p for p in points if p['id'] == 'native_extra_opportunity_bnn_01/runs/A0')
population = [p for p in points if p['circuit'] == 'bnn' and p['quality_cohort'] == anchor['quality_cohort']]
actor=D/'fused_resource_development_01/bnn_A0_native_only_K8'
domain_actor=D/'fused_resource_development_01/bnn_A0_feedback_K8'
terminal=read(actor/'completion.json');domain_terminal=read(domain_actor/'completion.json')
assert terminal['passed'] and domain_terminal['passed']
assert read(actor/'evaluation_context/input_seal.json')['passed'] and read(domain_actor/'evaluation_context/input_seal.json')['passed']
data = D / 'paper/data'
pdf = data / 'joint_quality_projection_34.pdf'
assert not pdf.exists()
unique = {}
for p in population:
    unique.setdefault((p['CPD_ns'], p['wirelength'], p['SB_pairs'], p['CB_sources']), p)
selected = [
    ('Budget64 full resource end', next(p for p in points if p.get('state')==read(D/'connection_budget_resource_dev_02/bnn_A0_paired/completion.json')['final_state']), '#006400', 'p'),
    ('R1 two-connection owner', next(p for p in points if p.get('arm')=='R1_partial_owner_native_2pins'), '#ca0020', '+'),
    ('Strong A0', anchor, 'black', 'D'),
    ('Strong R1', next(p for p in points if p['id']=='native_extra_opportunity_bnn_01/runs/R1'), '#4d4d4d', 's'),
    ('Timing first + native K8', next(p for p in points if p.get('state')==read(D/'strong_A0_native_only_K8_summary_01.json')['final_state']), '#1f77b4', 'o'),
    ('Timing first + guided K8', next(p for p in points if p.get('state')==read(D/'strong_A0_paired_K8_summary_01.json')['final_state']), '#9467bd', '*'),
    ('Imported native repair + timing', next(p for p in points if p['arm']=='complete_resource_native_then_current_STA_native'), '#2ca02c', 'P'),
    ('Imported guided repair + timing', next(p for p in points if p['arm']=='complete_resource_paired_then_current_STA_native'), '#d62728', '^'),
    ('R1 resource: fixed seeds', next(p for p in points if p.get('actor_final_selected') and p['batch']=='stable_seed_transfer_recovery_01'), '#008b8b', 'X'),
    ('R1 joint owner: native = domain', next(p for p in points if p['arm']=='R1_owner_escape_joint_native'), '#e31a1c', 'H'),
    ('R1 native seed terminal', next(p for p in points if p.get('state')==read(D/'native_checkpoint_recovery_03/bnn_R1_native/completion.json')['final_state']), '#7f0000', 'x'),
    ('Owner exchange: vector-rejected', next(p for p in points if p['arm']=='sealed_timing_proposal_05'), '#e377c2', 'h'),
    ('Tf native seed terminal', next(p for p in points if p['arm']=='Tf_native_recovery_final'), '#b15928', '1'),
    ('Tf resource (dominated)', next(p for p in points if p.get('actor_final_selected') and p['batch']=='stable_seed_transfer_recovery_02'), '#8c564b', '>'),
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
fig.savefig(data / 'joint_quality_projection_34.png', dpi=180, bbox_inches='tight')
plt.close(fig)
fields = ['id', 'arm', 'batch', 'convergence', 'opportunity', 'CPD_ns', 'wirelength', 'SB_pairs', 'CB_sources']
with (data / 'joint_quality_projection_34.csv').open('w') as stream:
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    writer.writerows({k: p[k] for k in fields} for p in population)
write(data / 'joint_quality_projection_binding_34.json', dict(passed=True, archive=str(archive),
    physical_quality_cohort=anchor['quality_cohort'], observations=len(population), unique_quality_tuples=len(unique),
    selected_records={name: p['id'] for name, p, _, _ in selected},
    source_sha256={str(p): sha(p) for p in [Path(__file__).resolve(), archive / 'completion.json', archive / 'points.json',archive/'verification.json',actor/'completion.json',actor/'attempts.json',actor/'evaluation_context/input_seal.json',domain_actor/'completion.json',domain_actor/'evaluation_context/input_seal.json',D/'low_resource_timing_accept_03.json']},
    artifact_sha256={n: sha(data / n) for n in ['joint_quality_projection_34.pdf', 'joint_quality_projection_34.png', 'joint_quality_projection_34.csv']},
    actual_cold_finals={row['arm']:{k:row[k] for k in ['id','CPD_ns','wirelength','SB_pairs','CB_sources','complete_single_configuration_seconds']} for row in population if row['arm'] in ['cold_full_native_resource_then_current_STA','cold_full_domain_resource_then_current_STA']},
    qualification='All actual legal BNN observations from the verified640-record archive, including all48budget64 candidates across two circuits and three partial-owner observations. Figure population includes BNN only; robot/eltwise stay in bound archive. Imported budget64 terminal costs are not cold complete costs. Old imported native/guided repair points remain explicitly labelled and do not inherit new full times. Both actual cold final quality points are part of the gray cloud and their own whole costs belong only to their actual case outputs; all intermediate/handoff/rejected states have unknown standalone full cost. Current legal archive excludes pending constructed wire/timing and escape-owner proposals. Existing A0/R1/U/Tf, fixed-seed roles, 47SB local menus, independent45SB feedback, rejected whole-net probes and checkpoint/pending native observations remain, without upgrading incomplete trajectories. Projection deduplicates exact four-axis quality coordinates only, not independent samples; endpoint-vector changes, phase binaries, opportunity and full costs stay in bound data. Quality projections are not two-dimensional or full-time Pareto boundaries. Shared-host/OS-cache effects and convergence differences preclude statistical speedup, per-circuit history-best configuration or one-factor domain/grouping attribution. Actual legacy metadata-cache dependencies are explicit in both case cost receipts; byte equality to own-command indexes does not make every consumer path internal. Fixed-device occupancy is not area/power.'))
print(dict(population=len(population), unique=len(unique), pdf=str(pdf)), flush=True)
