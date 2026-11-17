"""Fixed-CPD/CB projection of the already-admitted observations."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from retained_prefix_workflow import D,read,write,sha

out=D/'LSTM_admitted_mechanism_synthesis_01'
rows=read(out/'candidate_rows.json');steps=read(out/'accepted_steps.json')
fig,axes=plt.subplots(1,2,figsize=(11,4.7))
colors={'native':'#28649b','guided':'#c27320','fallback':'#25845b','owner':'#7c5896'}
for ax in axes:
    ax.axvline(2389,color='#777',ls='--',lw=1)
    ax.axvspan(2389,2900,color='#f5e7e7',alpha=.65)
    for group,color in colors.items():
        chosen=[r for r in rows if r['CPD_ns']==14.600438191791909 and r['CB_sources']==8316
                and ('owner' if r['role']=='joint_native' else 'native' if r['arm']=='native'
                     else 'guided' if r['role']=='reuse_on' else 'fallback')==group]
        for accepted in [False,True]:
            points=[r for r in chosen if r['original_status']=='legal_evaluated' and r['committed']==accepted]
            if points:ax.scatter([r['wire_delta_from_root'] for r in points],[r['SB_pairs'] for r in points],
                facecolors=color if accepted else 'none',edgecolors=color,s=32,zorder=4)
    bad=next(r for r in rows if r['original_status']=='FULL_STA_failed')
    ax.scatter([bad['wire_delta_from_root']],[bad['SB_pairs']],color='#b02035',marker='x',s=65,zorder=6)
    actual=[r for r in steps if r['arm']=='domain']
    ax.plot([0]+[r['wire_delta_from_root'] for r in actual]+[2184],
            [509]+[r['SB_pairs'] for r in actual]+[422],color='#555',lw=.7,zorder=1)
    ax.scatter([2184],[422],marker='*',s=130,color='#111',zorder=7)
    ax.set_xlabel('Wire increase relative to common root');ax.set_ylabel('Occupied SB pairs');ax.grid(alpha=.17)
axes[0].set(xlim=(-100,2900),ylim=(411,512),title='Actual trajectories and observed candidates')
axes[1].set(xlim=(2100,2890),ylim=(413,431),title='Budget boundary and fallback')
axes[1].annotate('Guided prefix: 427 SB\n41 wire units remain',(2348,427),xytext=(2120,429),arrowprops=dict(arrowstyle='-',lw=.6),fontsize=8)
axes[1].annotate('419 SB: +402 over cap\noriginal policy rejection',(2791,419),xytext=(2500,425),arrowprops=dict(arrowstyle='-',lw=.6),fontsize=8)
axes[1].annotate('Separate failed 419 SB\nraw evidence passed; never adopted',(2746,419),xytext=(2170,415),arrowprops=dict(arrowstyle='-',lw=.6),fontsize=8)
legend=[Line2D([],[],color=c,marker='o',ls='none',label=l) for c,l in zip(colors.values(),['Native control','Guided candidates','Native fallback','Owner proposals (none accepted)'])]
legend += [Line2D([],[],color='black',marker='o',ls='none',label='Filled: resource commit'),
           Line2D([],[],color='black',marker='o',mfc='none',ls='none',label='Open: policy rejection'),
           Line2D([],[],color='#b02035',marker='x',ls='none',label='Historical evaluation failure'),
           Line2D([],[],color='black',marker='*',ls='none',label='Admitted domain final'),
           Line2D([],[],color='#777',ls='--',label='Fixed 0.1% cap (ceil)')]
fig.legend(handles=legend,loc='lower center',ncol=3,fontsize=7,bbox_to_anchor=(.5,-.02))
fig.tight_layout(rect=(0,.17,1,1));fig.savefig(out/'complete_wire_SB_points.pdf',bbox_inches='tight');fig.savefig(out/'complete_wire_SB_points.png',dpi=170,bbox_inches='tight')
binding=read(out/'plot_binding.json');binding['source_sha256'][str(D/'plot_LSTM_admitted_mechanisms_01.py')]=sha(D/'plot_LSTM_admitted_mechanisms_01.py')
binding['owner_proposals_label_does_not_imply_acceptance']=True
write(out/'plot_binding.json',binding)
