#!/usr/bin/env python3
"""Export static research figures from validated study aggregates."""
import argparse
from pathlib import Path
from statistics import median

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from flatland_benchmark import BASE,read
from flatland_statistics import complete_circuits,paired
from lazagna_common import ROOT,sha256,utc,write_json

FAMILIES=['sb','cb_o','hybrid_o']
LABELS=dict(sb='SB',cb_o='CB-O',hybrid_o='Hybrid-O')
COLORS=dict(sb='#3671a8',cb_o='#c36a25',hybrid_o='#368b68')
CELLS=['p0_A0','p0_R1','p1_A0','p1_R1']


def save(fig,output,name):
    fig.savefig(output/(name+'.pdf'),bbox_inches='tight')
    fig.savefig(output/(name+'.svg'),bbox_inches='tight')
    fig.savefig(output/(name+'.png'),bbox_inches='tight',dpi=180)
    plt.close(fig)


def routing(summary,output):
    fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=True)
    for ax,flow in zip(axes,['p0','p1']):
        for i,f in enumerate(FAMILIES):
            data=summary['heldout'][f][flow]['routing_dual']['vs_3d']
            values=[r['ratio'] for r in data['per_circuit']]
            jitter=np.linspace(-.09,.09,len(values)) if values else []
            ax.scatter(i+np.asarray(jitter),values,s=15,alpha=.45,color=COLORS[f])
            if data['geomean_ratio'] is not None:
                ax.scatter(i,data['geomean_ratio'],marker='D',s=60,color=COLORS[f],edgecolor='black',zorder=3)
            ax.text(i,.01,f"n={len(values)}/{data['registered_circuits']}",ha='center',transform=ax.get_xaxis_transform(),fontsize=8)
        ax.axhline(1,color='#555',linestyle='--',linewidth=1)
        ax.set_xticks(range(3),[LABELS[f] for f in FAMILIES]);ax.set_title(flow.upper()+' placement')
        ax.grid(axis='y',alpha=.2)
    axes[0].set_ylabel('CPD ratio R1 / same-architecture A0 (lower is better)')
    fig.suptitle('Held-out routing effect: circuit means and geometric mean diamonds')
    save(fig,output,'routing_effect')


def rankings(summary,output):
    data=summary['architecture_rankings'];fig,axes=plt.subplots(1,2,figsize=(11,4))
    if data.get('status')!='complete_common_cohort_available':
        for ax in axes:ax.text(.5,.5,'No complete common circuit cohort',ha='center',va='center');ax.set_axis_off()
    else:
        for ax,metric,label in zip(axes,['absolute_geomean_cpd_ns','common_2d_geomean_ratio'],['CPD (ns)','CPD / common 2D reference']):
            for f in FAMILIES:
                values=[data['by_flow'][c][metric][f] for c in CELLS]
                ax.plot(range(4),values,'o-',label=LABELS[f],color=COLORS[f],linewidth=2)
                for seed,panel in data['by_seed'].items():
                    ax.scatter(range(4),[panel[c][metric][f] for c in CELLS],s=18,alpha=.3,color=COLORS[f])
            ax.set_xticks(range(4),[c.replace('_',' + ') for c in CELLS]);ax.set_ylabel(label)
            ax.grid(axis='y',alpha=.2)
        axes[0].legend(frameon=False)
    fig.suptitle(f"Architecture ordering on {len(data['complete_common_circuits'])}/{data['registered_circuits']} common circuits; dots include seed panels")
    save(fig,output,'architecture_ordering')


def ablations(summary,output):
    fig,axes=plt.subplots(1,3,figsize=(12,4),sharey=True)
    variants=['geometry','delay','critical','delay_critical'];labels=['G','D','C','D+C'];x=np.arange(4)
    for ax,f in zip(axes,FAMILIES):
        data=summary['ablations'][f];n=len(data['common_complete_circuits'])
        for kind,offset,color in [('fixed',-.17,'#929da6'),('tuned',.17,COLORS[f])]:
            values=[data['joint_cohort'][kind][v]['geomean_ratio'] for v in variants]
            ax.bar(x+offset,[v if v is not None else np.nan for v in values],width=.32,color=color,label=kind)
        ax.axhline(1,color='#555',linestyle='--',linewidth=1)
        ax.set_xticks(x,labels);ax.set_title(f'{LABELS[f]}: n={n}/14 common circuits')
        ax.grid(axis='y',alpha=.2)
        if n==0:ax.text(.5,.5,'No complete common cohort',ha='center',transform=ax.transAxes)
    axes[0].set_ylabel('CPD / P1 A0 (lower is better)');axes[-1].legend(frameon=False)
    fig.suptitle('Held-out ablations, seed 21: fixed config 0 and equal-budget tuning')
    save(fig,output,'ablations')


def runtime(serial,output):
    circuits=list(dict.fromkeys(c['circuit'] for c in serial['cases']))
    fig,axes=plt.subplots(1,len(circuits),figsize=(6*len(circuits),4),squeeze=False)
    timing={(r['circuit'],r['family'],r['flow']):r for r in serial['comparisons']['R1_over_A0']['per_case']}
    for ax,circuit in zip(axes[0],circuits):
        count=0
        for case in [c for c in serial['cases'] if c['circuit']==circuit]:
            t=timing[circuit,case['family'],case['flow']]
            if t['paired_legal_repeats']!=3:continue
            a=median(r['routes']['R1']['metrics']['critical_path_ns'] for r in case['repeats'])
            b=median(r['routes']['A0']['metrics']['critical_path_ns'] for r in case['repeats'])
            x=t['router']['ratio'];y=a/b;f=case['family'];flow=case['flow'];count+=1
            ax.scatter(x,y,color=COLORS[f],marker='o' if flow=='p0' else '^',s=55)
            ax.annotate(LABELS[f]+' '+flow.upper(),(x,y),xytext=(4,4),textcoords='offset points',fontsize=7)
        ax.axhline(1,color='#555',linestyle='--',linewidth=1);ax.axvline(1,color='#555',linestyle='--',linewidth=1)
        ax.set_xlabel('Median router time R1 / A0');ax.set_ylabel('CPD R1 / A0');ax.set_title(f'{circuit}: {count}/6 complete cases')
        ax.grid(alpha=.2)
    fig.suptitle('Serial subset: three repeats per case; lower/left is better')
    save(fig,output,'runtime_quality')


def training(protocol,output):
    variants=list(protocol['tuning']['variants']);circuits=protocol['training'];rows={}
    for f in FAMILIES:
        tables={('A0',None):{}}
        tables.update({(v,i):{} for v in variants for i in range(8)})
        for circuit in circuits:
            path=BASE/'training_cases'/f'{circuit}_{f}'/'audit_summary.json';audit=read(path)
            assert audit['passed'] and audit['registered_route_count']==33
            for r in audit['legal']:
                tags=read(BASE/'runs'/r['name']/'manifest.json')['tags']
                key=('A0',None) if tags['router']=='A0' else (tags['variant'],tags['config'])
                tables[key][circuit,11]=dict(status='legal',metrics=r['metrics'],run=r['name'])
        common=complete_circuits(list(tables.values()),circuits,[11]);matrix=[];legal=[]
        for v in variants:
            matrix.append([paired(tables[v,i],tables['A0',None],circuits,[11],cohort=common)['geomean_ratio'] for i in range(8)])
            legal.append([len(tables[v,i]) for i in range(8)])
        rows[f]=dict(common=common,ratios=matrix,legal_counts=legal)
    fig,axes=plt.subplots(1,3,figsize=(13,4));flat=[x for r in rows.values() for line in r['ratios'] for x in line if x is not None]
    delta=max([abs(x-1) for x in flat]+[.01])
    for ax,f in zip(axes,FAMILIES):
        row=rows[f];data=np.array([[x if x is not None else np.nan for x in line] for line in row['ratios']])
        im=ax.imshow(data,cmap='RdBu_r',vmin=1-delta,vmax=1+delta,aspect='auto')
        for v in range(4):
            for i in range(8):
                value=data[v,i];label=f'{value:.3f}' if np.isfinite(value) else 'NA'
                ax.text(i,v,label+'\n'+str(row['legal_counts'][v][i])+'/6',ha='center',va='center',fontsize=6)
        ax.set_xticks(range(8));ax.set_yticks(range(4),['G','D','C','D+C']);ax.set_xlabel('Registered configuration ID')
        ax.set_title(f"{LABELS[f]}: common n={len(row['common'])}/6")
    fig.colorbar(im,ax=axes.tolist(),label='Training CPD / A0',shrink=.7)
    fig.suptitle('Training exploration only: common-cohort ratios and legal counts')
    save(fig,output,'training_search');write_json(output/'training_plot_data.json',rows)


def main(output):
    output=Path(output);assert not output.exists()
    paths={name:BASE/path for name,path in [('evaluation','evaluation_analysis/summary.json'),
        ('serial','serial_analysis/summary.json'),('protocol','benchmark_protocol.json')]}
    data={k:read(p) for k,p in paths.items()}
    assert data['evaluation']['status']=='all_registered_evaluation_cases_resolved'
    assert data['serial']['observed_repetitions']==36
    output.mkdir(parents=True,exist_ok=False)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'pdf.fonttype':42,'svg.fonttype':'none'})
    routing(data['evaluation'],output);rankings(data['evaluation'],output);ablations(data['evaluation'],output)
    runtime(data['serial'],output);training(data['protocol'],output)
    write_json(output/'manifest.json',dict(utc=utc(),source_sha256=sha256(__file__),matplotlib=matplotlib.__version__,
        numpy=np.__version__,input_sha256={str(p):sha256(p) for p in paths.values()},
        artifact_sha256={p.name:sha256(p) for p in output.iterdir() if p.is_file()},
        notes='No inference from parallel runtime. Every plot labels its complete cohort; missing values are not zero. Training search points vary multiple parameters and do not identify individual causal parameter effects.'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=BASE/'figures')
    main(p.parse_args().output)
