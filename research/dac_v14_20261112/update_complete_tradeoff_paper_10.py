"""Build a complete-pair figure from sealed evidence; preserve the historical plot."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
import re
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from retained_prefix_workflow import D, read, write, sha

p = D/'paper'
parent_path = D/'owner_contract_paper_binding_09.json'
parent = read(parent_path)
previous = Path(parent['snapshot'])
e = D/'complete_tradeoff_paper_evidence_10'
assert not (D/'complete_tradeoff_paper_binding_10.json').exists()
assert sha(p/'current_repair_main.tex') == sha(previous/'current_repair_main.tex')
e.mkdir(exist_ok=True)
sources = [parent_path, previous/'data/complete_table_rows.json',
           previous/'data/new_complete_input_rows.json', previous/'data/input_failure_rows.json',
           D/'complete_BNN_cost_hierarchy_01/completion.json']
rows = {}
for path in sources[1:4]:
    for row in read(path):
        rows[row['label']] = row
def arm(label):
    row = rows[label]
    quality = row.get('quality')
    if quality is None and row.get('resources') is not None:
        quality = dict(row['resources'], CPD_ns=row['CPD_ns'])
    assert quality is not None, label
    return dict(label=label, quality=quality,
                seconds=row.get('complete_seconds', row.get('time_seconds')))

pairs = []
for label, prefix in [('BNN', 'BNN cold'), ('Eltwise', 'Eltwise'), ('Robot', 'Robot'),
                      ('Robot SDC', 'Robot SDC'), ('Softmax', 'Softmax'), ('SPMV', 'SPMV'),
                      ('Eltwise SB', 'SB-only'), ('Eltwise SB 102%', 'SB 102\\%'),
                      ('Eltwise CB', 'CB-only')]:
    n, d = arm(prefix+' N'), arm(prefix+' D')
    nq, dq = n['quality'], d['quality']
    delta = {k: dq[k]-nq[k] for k in nq}
    pct = dict(vertical=100*(delta['SB_pairs']+delta['CB_sources'])/(nq['SB_pairs']+nq['CB_sources']),
               wire=100*delta['wirelength']/nq['wirelength'],
               CPD=100*delta['CPD_ns']/nq['CPD_ns'], time=100*(d['seconds']/n['seconds']-1))
    pairs.append(dict(label=label, native=n, domain=d, delta=delta, percent=pct))
assert len(pairs) == 9
assert all(x['percent']['CPD'] == 0 for x in pairs if x['label'] != 'Eltwise SB 102%')
assert pairs[0]['delta']['SB_pairs'] == -39 and pairs[0]['delta']['CB_sources'] == -2
failures = [dict(label=k, quality=None, seconds=v.get('complete_seconds', v.get('time_seconds')))
            for k,v in rows.items() if '(initial fail)' in k or '(load fail)' in k]
assert len(failures) == 8
assert all(v.get('quality') is None and v.get('resources') is None
           for k,v in rows.items() if '(initial fail)' in k or '(load fail)' in k)
write(e/'paired_complete_deltas.json', pairs)
write(e/'failed_complete_attempts.json', failures)

plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':7.2,
                     'axes.labelsize':7.2, 'axes.titlesize':7.5, 'pdf.fonttype':42})
fig, axes = plt.subplots(1, 4, figsize=(7.1, 3.65), sharey=True)
fig.subplots_adjust(left=.245, right=.985, bottom=.19, top=.86, wspace=.43)
specs = [('vertical', 'SB + CB', (-.94,.31), [-.8,-.4,0], 3),
         ('wire', 'Wire', (-.012,.119), [0,.05,.10], 3),
         ('CPD', 'CPD', (-.12,1.64), [0,.6,1.2], 3),
         ('time', 'Complete time', (-6,50), [0,20,40], 2)]
for ax, (key,title,limits,ticks,digits) in zip(axes,specs):
    for y, row in enumerate(pairs):
        value = row['percent'][key]
        color = '#176b55' if value < 0 else '#a04b20' if value > 0 else '#56616c'
        ax.axhspan(y-.45,y+.45,color='#f5f6f7' if y%2==0 else 'white',zorder=0)
        ax.plot([0,value],[y,y],color=color,lw=1.5,zorder=3)
        ax.scatter([value],[y],s=14,color=color,zorder=4)
        txt = '0' if value == 0 else f'{value:+.{digits}f}'
        # Values use the same horizontal offset in points, preserving data scale.
        ax.annotate(txt,(value,y),xytext=(4,0),textcoords='offset points',
                    va='center',ha='left',fontsize=6.7,color=color,
                    bbox=dict(facecolor='white',edgecolor='none',pad=.15,alpha=.97))
    ax.axvline(0,color='#939ba2',lw=.7,zorder=1)
    ax.set_xlim(*limits);ax.set_xticks(ticks);ax.set_ylim(8.6,-.7)
    ax.set_title(title,pad=6,fontweight='bold')
    ax.set_xlabel('Change (%)')
    ax.tick_params(axis='y',length=0)
    ax.tick_params(axis='x',labelsize=6.8)
    for side in ['top','right','left']: ax.spines[side].set_visible(False)
    ax.spines['bottom'].set_color('#aeb4ba')
axes[0].set_yticks(range(9))
axes[0].set_yticklabels([f"{r['label']}  [{r['delta']['SB_pairs']:+d}, {r['delta']['CB_sources']:+d}]" for r in pairs])
fig.text(.018,.91,'Input / configuration [SB, CB count change]',fontsize=7.1)
fig.text(.57,.955,'Domain-first minus native; each row has its own native denominator',
         ha='center',fontsize=8)
fig.text(.018,.054,'Both arms failed: Conv-layer / Attention (initial routing); CLSTM / Robot p1 (input loading).',fontsize=7)
fig.text(.018,.018,'No quality deltas for failed attempts. Rows are configurations, not independent samples. Time is descriptive.',fontsize=7)
figure=p/'data/complete_paired_tradeoffs_10.pdf'
fig.savefig(figure,metadata={'CreationDate':None,'ModDate':None})
fig.savefig(e/'complete_paired_tradeoffs_10.png',dpi=180)
plt.close(fig)

old=(previous/'current_repair_main.tex').read_text()
new=old.replace('Independent feedback improves ten setup components',
                'Separate fixed-input feedback improves ten setup components')
oldfigure=re.findall(r'\\begin\{figure\*\}.*?\\end\{figure\*\}', old,re.S)
assert len(oldfigure)==1
replacement=r'''\begin{figure*}[t]
\centering\includegraphics[width=.98\textwidth]{data/complete_paired_tradeoffs_10.pdf}
\caption{Complete domain-first/native tradeoffs from Table~\ref{tab:completecost}: $100(D-N)/N$ within each matched pair. Brackets report separate SB/CB count changes. Each panel has its own scale; lower is better for that metric. Nine legal configuration pairs are not nine independent inputs. Eight failed attempts retain costs in the table and have no quality deltas. Single-run time differences are descriptive, not statistical speedups.}
\label{fig:joint}
\end{figure*}'''
new=new.replace(oldfigure[0],replacement)
oldsentence='The archive projection retains dominated and rejected legal candidates with input identities and full vectors; coincident points are not independent samples and two-dimensional projections are not Pareto frontiers.'
assert oldsentence in new
new=new.replace(oldsentence,'Figure~\\ref{fig:joint} instead compares complete paired outcomes across circuits and configurations, retaining no-gain cases and failures. Historical local projections, dominated/rejected candidates and their full vectors remain in the supplement; coincident points add no independent samples.')
anchor='Acceptance-ordered execution skips an optional native diagnostic only after the domain candidate passes full resource acceptance.'
assert new.count(anchor)==1
costparagraph=('In the original BNN pair, resource transactions account for 1692.84 s of the observed 1821.07-s total difference (92.96\\%). Native/domain execute 70/1361 connection queries, counting repeated queries separately. Nested native-core times are 38.23/1207.26 s and cannot be added to complete costs. This decomposition identifies the dominant work, not a new speedup.\n\n')
new=new.replace(anchor,costparagraph+anchor)
source=p/'current_repair_complete_tradeoffs_10.tex';source.write_text(new)
(e/'historical_figure.tex').write_text(oldfigure[0]+'\n')
sources += [source, figure, e/'paired_complete_deltas.json',e/'failed_complete_attempts.json',Path(__file__).resolve()]
write(e/'edit_registration.json',dict(parent=str(parent_path),source=str(source),
    matched_legal_configuration_pairs=9,failed_attempts_retained=8,
    complete_table_rows_unchanged=33,new_native_calls=0,new_independent_results=0,
    source_sha256={str(f):sha(f) for f in sources},
    historical_figure_preserved=str(previous/'data/joint_quality_projection_34.pdf'),
    qualification='Reorganizes existing verified complete evidence; no new scientific outcomes or universal benefit. Different configurations of one circuit are not independent inputs. Original22.95% cost remains; active engineering result pending.'))
print(dict(source=str(source),figure=str(figure),legal_pairs=len(pairs),failed_attempts=len(failures)))
