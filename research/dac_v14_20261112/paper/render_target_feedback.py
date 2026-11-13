#!/usr/bin/env python3
"""Render sealed paired development evidence, with source hashes and no timing claim."""
from pathlib import Path
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

P = Path(__file__).resolve().parent
D = P.parent
files = [D/'target_feedback_circuit_summary.json', D/'refresh_assignment_circuit_summary.json']
feedback, ablation = [json.loads(p.read_text()) for p in files]
f = {(r['circuit'], r['arm']): r for r in feedback['observations']}
a = {(r['circuit'], r['arm']): r for r in ablation['observations']}
circuits = ['spmv', 'softmax', 'eltwise_layer', 'bnn']
rows = []
for c in circuits:
    assert f[c, 'Tf']['metrics']['critical_path_ns'] == a[c, 'Tf']['metrics']['critical_path_ns']
    assert f[c, 'Tf']['metrics']['iterations'] == a[c, 'Tf']['metrics']['iterations']
    for arm, source in [('V', f[c, 'V']), ('Tf', a[c, 'Tf']), ('Ri', a[c, 'Ri'])]:
        assert source['status'] == 'legal'
        rows.append(dict(circuit=c, arm=arm, cpd_ns=source['metrics']['critical_path_ns'],
                         iterations=source['metrics']['iterations'], source=source['path']))
index = {(r['circuit'], r['arm']): r for r in rows}
plt.rcParams.update({'font.size': 8, 'pdf.fonttype': 42, 'ps.fonttype': 42})
fig, axes = plt.subplots(1, 2, figsize=(7.1, 2.5), layout='constrained')
x = np.arange(len(circuits))
for offset, arm, color, label in [(-.22, 'V', '#657a8e', 'Full-net refresh'),
                                 (0., 'Tf', '#287e67', 'Target refresh (Tf)'),
                                 (.22, 'Ri', '#c08038', 'Tf, independent refresh (Ri)')]:
    cpds = [100 * (index[c, arm]['cpd_ns']/index[c, 'V']['cpd_ns'] - 1) for c in circuits]
    axes[0].plot(x+offset, cpds, 'o', color=color, label=label, markersize=5)
    axes[1].bar(x+offset, [index[c, arm]['iterations'] for c in circuits], .21, color=color)
axes[0].axhline(0, color='#444444', linewidth=.7, linestyle='--')
axes[0].set_ylabel('CPD change vs full-net refresh (%)')
axes[0].set_ylim(-3.15, .65)
axes[0].set_title('(a) Lower is better')
axes[1].set_ylabel('Native routing iterations')
axes[1].set_title('(b) Convergence cost')
for ax in axes:
    ax.set_xticks(x, ['spmv', 'softmax', 'eltwise', 'bnn'])
    ax.spines[['top', 'right']].set_visible(False)
fig.legend(*axes[0].get_legend_handles_labels(), loc='outside upper center', ncol=3,
           frameon=False, fontsize=8)
for suffix in ['pdf', 'png']:
    fig.savefig(P/f'figures/target_feedback_ablation.{suffix}', dpi=180)
out = dict(scope='Four seen seed11 HybridO/P0/W100 circuits; all plotted roles legal. '
           'Strictly matched reused controls; no blind-test or formal runtime claim. '
           'CPD rounded to native reported precision, ties plotted explicitly.',
           observations=rows, source_sha256={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
           script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
(P/'data/target_feedback_figure.json').write_text(json.dumps(out, indent=2)+'\n')
