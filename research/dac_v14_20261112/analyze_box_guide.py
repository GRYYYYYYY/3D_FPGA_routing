#!/usr/bin/env python3
import collections,resource,signal
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha,route_body
from analyze_native_reconvergence_v2 import observe
from verify_path_witnesses_v2 import fields,graph_records,f32
from analyze_search_domain_v2 import inside
from bounded_critical_records import records
from routing_log_metrics import ROW

def main():
    resource.setrlimit(resource.RLIMIT_AS,(16*1024**3,16*1024**3));signal.alarm(1800)
    b=D/'box_guide_eltwise_dev_01';assert read(b/'input_seal.json')['passed'];done=read(b/'completion.json');assert done['disabled_gate_passed'] and not done['missing_arms'];reg=read(b/'registration.json')
    dirs={a:b/'runs'/('eltwise_layer_'+a) for a in reg['arms']};logs={a:(rd/'stdout.log').read_text().splitlines() for a,rd in dirs.items()}
    domains={a:[fields(l) for l in lines if l.startswith('H3D_SEARCH_DOMAIN ')] for a,lines in logs.items()};suppressed={a:[fields(l) for l in lines if l.startswith('H3D_BOX_GUIDE_SUPPRESSED ')] for a,lines in logs.items()};prefs={int(n) for rows in domains.values() for r in rows if r['preferred']!='-' for n in r['preferred'].split(',')}
    m=read(dirs['C2']/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);bindings={str(p):sha(p) for p in [Path(__file__),Path(inside.__code__.co_filename),graph,b/'registration.json',b/'completion.json',b/'input_seal.json',D/'box_guide_experiment_01.json',D/'search_domain_eltwise_dev_01/search_domain_analysis.json']}
    assert sha(graph)==m['shared_inputs'][str(graph)]['sha256']
    nodes={};layers=0;cross=collections.defaultdict(list)
    for section,e in graph_records(graph):
        at=e.attrib
        if section=='rr_nodes':
            node=int(at['id']);v=e.find('loc').attrib;layer=int(v.get('layer_low',v.get('layer',0)));assert layer==int(v.get('layer_high',v.get('layer',0)));layers=max(layers,layer+1);nodes[node]=dict(layer=layer,direction=at.get('direction','NONE'),**{k:int(v[k]) for k in ['xlow','xhigh','ylow','yhigh']})
        elif section=='rr_edges':
            u,v=int(at['src_node']),int(at['sink_node'])
            if u in prefs and nodes[u]['layer']!=nodes[v]['layer']:cross[u].append(v)
    details={};rows=[]
    for a,rd in dirs.items():
        m=read(rd/'manifest.json');env=m['environment'];assert env['VPR_H3D_BOX_GUIDE_ADMISSION']==('0' if a=='C2' else '1') and 'VPR_H3D_BOUNDED_CRITICAL_GUIDE' not in env
        assert env['VPR_H3D_TRACE_SEARCH_DOMAIN']==env['VPR_H3D_TRACE_GUIDE_INFLUENCE']=='1';assert env['VPR_H3D_CANDIDATE_PATH_SCORE']==env['VPR_H3D_CANDIDATE_PATH_DELAY']==env['VPR_H3D_SOURCE_COVERAGE_SKIP']=='0'
        count=1 if a=='B1' else 2;assert m['command'][m['command'].index('--router_max_convergence_count')+1]==str(count)
        row=dict(observe(rd),arm=a,count=count,reused=False);rows.append(row)
        for n in ['manifest.json','stdout.log','independent_audit.json','h3d_final_guides.csv','final_guide_audit.json','first_legal_prefix_reproduction.json','disabled_reproduction.json']:
            if (rd/n).exists():bindings[str(rd/n)]=sha(rd/n)
        search_summary=[fields(l) for l in logs[a] if l.startswith('H3D_SEARCH_DOMAIN_SUMMARY ')]
        assert search_summary and int(search_summary[-1]['rows'])==len(domains[a]) and int(search_summary[-1]['omitted'])==0
        eligible=[]
        for r in domains[a]:
            pref=[] if r['preferred']=='-' else list(map(int,r['preferred'].split(',')))
            pi=sum(inside(nodes[n],r,layers) for n in pref);heads=sum(len(cross[n]) for n in pref);admitted=sum(inside(nodes[n],r,layers) and (int(r['rcv']) or inside(nodes[v],r,layers)) for n in pref for v in cross[n])
            assert (pi,heads,admitted)==tuple(int(r[k]) for k in ['preferred_inside','crossing_heads','admitted_heads'])
            if int(r['guide']) and not int(r['rcv']) and admitted==0:eligible.append(r)
        apply=suppressed[a];assert len({r['search'] for r in apply})==len(apply)
        assert {r['search'] for r in apply}==({r['search'] for r in eligible} if a!='C2' else set())
        by={r['search']:r for r in eligible}
        for r in apply:assert all(r[k]==by[r['search']][k] for k in ['iter','attempt','search','net','pin'])
        summary=[fields(l) for l in logs[a] if l.startswith('H3D_BOX_GUIDE_SUMMARY ')]
        if a=='C2':assert not summary
        else:assert summary and int(summary[-1]['suppressed'])==int(summary[-1]['rows'])==len(apply) and int(summary[-1]['omitted'])==0
        details[a]=dict(domain_rows=len(domains[a]),BB_excluded_guided_searches=len(eligible),suppressed=len(apply),affected_nets=len({r['net'] for r in apply}),firstlegal_prefix_verified=read(rd/'first_legal_prefix_reproduction.json')['passed'] if (rd/'first_legal_prefix_reproduction.json').exists() else None)
    reused=[dict(observe(Path(p)),arm=a,count=int(c),reused=True) for c,rs in reg['references'].items() for a,p in rs.items()]
    reused += [dict(observe(Path(p)),arm=a,count=int(c),reused=True) for c,rs in reg['controls'].items() for a,p in rs.items()]
    pairs={}
    for a in ['B2','B1']:
        tr=next(r for r in rows if r['arm']==a)
        for cr in [r for r in reused if r['count']==tr['count'] and r['arm'] in ['C','A0','R1','A1']]:
            ok=tr['status']==cr['status']=='legal';pairs[f"count{tr['count']}:{cr['arm']}->{a}"]=dict(comparable=ok,reference_cpd_ns=cr['legal_cpd_ns'],new_cpd_ns=tr['legal_cpd_ns'],cpd_improvement_pct=(1-tr['legal_cpd_ns']/cr['legal_cpd_ns'])*100 if ok else None)
    for r in reused:
        rd=Path(r['path'])
        for n in ['manifest.json','independent_audit.json','final_guide_audit.json']:
            if (rd/n).exists():bindings[str(rd/n)]=sha(rd/n)
    equivalence={}
    for a,count in [('B2',2),('B1',1)]:
        ref=dirs['C2'] if count==2 else Path(reg['controls']['1']['C']);x=logs[a];y=(ref/'stdout.log').read_text().splitlines()
        norm=lambda ls:records([l for l in ls if not l.startswith(('H3D_BOX_GUIDE','H3D_SEARCH_DOMAIN'))])
        equivalence[a]=dict(original_cost_records=norm(x)==norm(y),prefix=[l for l in x if l.startswith('H3D_PREFIX_')]==[l for l in y if l.startswith('H3D_PREFIX_')],numeric_rows=[l.split()[:1]+l.split()[2:] for l in x if ROW.match(l)]==[l.split()[:1]+l.split()[2:] for l in y if ROW.match(l)],complete_route=route_body(dirs[a]/'routed.route')==route_body(ref/'routed.route'),final_guide_csv=sha(dirs[a]/'h3d_final_guides.csv')==sha(ref/'h3d_final_guides.csv'),actual_influence=[l for l in x if l.startswith('H3D_GUIDE_INFLUENCE_')]==[l for l in y if l.startswith('H3D_GUIDE_INFLUENCE_')])
    assert all(sha(p)==h for p,h in bindings.items());write(b/'box_guide_analysis.json',dict(passed=True,status='sealed_box_guide_development',details=details,equivalence=equivalence,observations=rows+reused,comparisons=pairs,source_sha256=bindings,qualification='Actual search-local preference suppression only where independent RRG native drivepoint BB tests reject all preferred source/head pairs; no assertion of connectivity if admitted, RCV excluded. All persisted suppression decisions audited, source configuration/control/prefix/native/full graph/guide/input audits. One seen circuit and separate stopping rules; development times not formal speedup. Planned final guides remain intact even when preference locally suppressed, so final adoption is not per-search application evidence. No attribution from route changes to one event.'))
    print(dict(details=details,comparisons=pairs,rows=rows))
if __name__=='__main__':main()
