#!/usr/bin/env python3
"""Plot all matched legal BNN quality groups, including strong native baselines."""
import collections
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize
from matplotlib.lines import Line2D
from retained_prefix_workflow import D,read,write,sha
b=D/'joint_resource_tradeoff_plot_02';b.mkdir(exist_ok=False);archive=D/'multiobjective_archive_28';points=[p for p in read(archive/'points.json') if p['circuit']=='bnn'];assert len({p['quality_cohort'] for p in points})==1;groups=collections.defaultdict(list)
for p in points:groups[p['CPD_ns'],p['wirelength'],p['SB_pairs'],p['CB_sources']].append(p)
fig,ax=plt.subplots(figsize=(8.8,5.5));ordered=sorted(groups.items());color_min=min(k[3] for k,_ in ordered);color_max=max(k[3] for k,_ in ordered);last=None;data=[]
for key,group in ordered:
 cpd,wire,sb,cb=key;baseline=any(p['arm'] in ['A0','R1'] for p in group);frontier=any(not p['quality_dominated_by'] for p in group);size=30+sb*.48;marker='*' if baseline else 'o';last=ax.scatter([cpd],[wire/1e6],c=[cb],s=size*(2.1 if baseline else 1),cmap='viridis_r',vmin=color_min,vmax=color_max,marker=marker,alpha=1 if baseline or frontier else .25,edgecolors='black' if baseline else '#444444',linewidths=.45,zorder=4 if baseline else 2)
 low=min(p['CPD_interval_ns'][0] for p in group);high=max(p['CPD_interval_ns'][1] for p in group);ax.errorbar(cpd,wire/1e6,xerr=[[cpd-low],[high-cpd]],fmt='none',ecolor='#555555',linewidth=.5,zorder=1);data.append(dict(CPD_ns=cpd,CPD_interval_ns=[low,high],wirelength=wire,SB_pairs=sb,CB_sources=cb,baseline=baseline,frontier_or_precision_uncertain=frontier,observation_ids=[p['id'] for p in group]))
labels=[('R1 strict',13.228145689936355,2068880,(8,20)),('A0 native, 8 opportunities',13.607436066820355,2059567,(-170,12)),('Old reassignment: CB5059',13.4216,2072203,(15,20))]
for label,x,y,offset in labels:ax.annotate(label,(x,y/1e6),xytext=offset,textcoords='offset points',fontsize=8,arrowprops=dict(arrowstyle='-',linewidth=.6,color='#555555'))
ax.set_xlabel('Final CPD (ns), lower is better');ax.set_ylabel('Planar wirelength (million units), lower is better');ax.grid(alpha=.2);fig.colorbar(ScalarMappable(norm=Normalize(color_min,color_max),cmap='viridis_r'),ax=ax,label='Actual CB sources occupied');ax.legend(handles=[Line2D([0],[0],marker='*',linestyle='',color='black',markersize=11,label='A0/R1 native baselines (including added opportunity)'),Line2D([0],[0],marker='o',linestyle='',color='#666666',markersize=6,label='Other legal states; marker size increases with actual SB')],loc='upper left',fontsize=7)
fig.suptitle('Joint BNN quality observations under matched physical inputs',fontsize=12);fig.text(.02,.01,'Different code, convergence and repair opportunities remain separate observations. Faint: certainly quality-dominated.\nCPD print uncertainty is retained. This is a quality projection; unknown complete runtime is not a zero cost.',fontsize=7);fig.tight_layout(rect=[0,.06,1,.95]);fig.savefig(b/'joint_quality.png',dpi=180);fig.savefig(b/'joint_quality.pdf');plt.close(fig);write(b/'plot_data.json',data);write(b/'completion.json',dict(passed=True,archive=str(archive),observations=len(points),distinct_scalar_quality_groups=len(groups),source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),archive/'points.json',archive/'completion.json']},artifact_sha256={n:sha(b/n) for n in ['joint_quality.png','joint_quality.pdf','plot_data.json']},native_calls=0,qualification='Complete matched BNN collected quality population includes strong A0/R1 and original-native extra opportunity, not only the method internal frontier. Colors and size show actual fixed-architecture resource use, not area or power. Rounded uncertainties and whole-runtime unknowns preserved. No per-circuit historical-best algorithm selection.'))
print(dict(observations=len(points),groups=len(groups)),flush=True)
