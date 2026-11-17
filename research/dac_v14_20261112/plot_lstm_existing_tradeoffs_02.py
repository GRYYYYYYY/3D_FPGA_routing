"""Plot observed discrete points only; do not interpolate feasible routes."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

out=D/'LSTM_existing_tradeoffs_02';rows=read(out/'candidate_rows.json')
for suffix in ['pdf','png']:
    p=out/('wire_SB_working_points.'+suffix)
    p.rename(out/('wire_SB_working_points_initial.'+suffix))
front=[r for r in rows if r.get('wire_SB_projected_nondominated')]
focus=read(out/'focused_419_SB_candidate.json')
fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
for ax in axes:
    ax.axvspan(-100,2389,color='#edf5ec',zorder=0)
    ax.axvline(2389,color='black',linestyle='--',linewidth=1,label='registered 0.1% cap (+2389)')
    for search,color,marker in [('guided','#276ca4','s'),('native','#bd671a','o')]:
        rr=[r for r in rows if r['search']==search]
        ax.scatter([r['wire_delta_from_root'] for r in rr],[r['SB_pairs'] for r in rr],s=28,
            facecolors=color,edgecolors='white',linewidths=.4,marker=marker,label=search+' candidates')
    xy=sorted(set((r['wire_delta_from_root'],r['SB_pairs']) for r in front))
    ax.scatter([x for x,y in xy],[y for x,y in xy],s=60,facecolors='none',edgecolors='#555555',
        linewidths=.6,label='observed W/SB front (same CPD/CB)')
    ax.set_xlabel('Wire increment from fixed root');ax.set_ylabel('SB occupancy');ax.grid(alpha=.2)
axes[0].scatter([0],[509],color='black',marker='*',s=65,label='fixed root')
axes[0].set_title('Closed legal candidate observations')
axes[0].set_xlim(min(-30,min(r['wire_delta_from_root'] for r in rows)-50),max(r['wire_delta_from_root'] for r in rows)+80)
axes[1].set_xlim(2100,2950);axes[1].set_ylim(416,437);axes[1].set_title('Original budget boundary (zoom)')
axes[1].annotate('419 SB / +402 over cap',xy=(focus['wire_delta_from_root'],419),xytext=(2440,417),fontsize=8,arrowprops=dict(arrowstyle='->',lw=.7))
native=[r for r in rows if r['id']=='domain/round_012/candidate_02/reuse_off'][0]
axes[1].annotate('native 425 SB, accepted',xy=(native['wire_delta_from_root'],425),xytext=(2120,432),fontsize=8,arrowprops=dict(arrowstyle='->',lw=.7))
axes[0].legend(fontsize=7,loc='best')
fig.savefig(out/'wire_SB_working_points.pdf');fig.savefig(out/'wire_SB_working_points.png',dpi=170);plt.close(fig)
write(out/'plot_binding.json',dict(passed=True,discrete_observations_only=True,interpolated_routes_claimed=False,
    projected_front_excludes_different_CPD_or_CB=True,endpoint_dominance_claimed=False,
    source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),out/'candidate_rows.json',out/'focused_419_SB_candidate.json',out/'wire_SB_working_points.pdf',out/'wire_SB_working_points.png']}))
print(dict(points=len(rows),interpolation=False))
