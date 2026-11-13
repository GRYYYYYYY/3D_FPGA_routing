#!/usr/bin/env python3
"""Render completed strict serial measurements; no solver invocation."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
p=Path(__file__).resolve().parent
s=json.loads((p/'data/evidence_snapshot.json').read_text())
rows=[r for r in s['serial']['comparisons']['R1_over_A0']['per_case'] if r['paired_legal_repeats']==3]
labels=[('spmv' if r['circuit']=='spmv' else 'robot')+' '+{'sb':'SB','cb_o':'CB-O','hybrid_o':'H-O'}[r['family']]+'/'+r['flow'].upper() for r in rows]
plt.rcParams.update({'font.size':8,'pdf.fonttype':42,'ps.fonttype':42})
fig,ax=plt.subplots(figsize=(3.5,2.2),layout='constrained')
y=np.arange(len(rows))
ax.barh(y-.16,[r['router']['ratio'] for r in rows],height=.3,label='Router',color='#385b80')
ax.barh(y+.16,[r['route_process']['ratio'] for r in rows],height=.3,label='Route process',color='#c89136')
ax.axvline(1,color='#444444',linewidth=.7,linestyle='--')
ax.set_yticks(y,labels);ax.invert_yaxis();ax.set_xlim(0,3.65);ax.set_xticks([0,1,2,3]);ax.set_xlabel('Median time ratio R1 / A0 (lower is faster)')
ax.legend(loc='lower center',bbox_to_anchor=(0.5,1.01),ncol=2,fontsize=7,frameon=False);ax.spines[['top','right']].set_visible(False)
fig.savefig(p/'figures/strict_runtime.pdf');fig.savefig(p/'figures/strict_runtime.png',dpi=180)
