#!/usr/bin/env python3
import collections,math,os,resource,shutil,signal,struct,subprocess,time
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from verify_path_witnesses_v2 import fields,graph_records,f32

def main():
    resource.setrlimit(resource.RLIMIT_AS,(24*1024**3,24*1024**3));signal.alarm(1800);assert shutil.disk_usage(D).free>=80*1024**3
    out=D/'residual_query_offline_01';out.mkdir(exist_ok=False);(out/'src').mkdir()
    protocol=read(D/'residual_multitarget_query_experiment_01.json');b=D/'search_domain_eltwise_dev_01';rd=b/'runs/eltwise_layer_T';m=read(rd/'manifest.json');graph=Path(m['command'][m['command'].index('--read_rr_graph')+1]);oracle=read(D/'residual_seed_oracle_01/analysis.json');assert oracle['passed'] and sha(D/'residual_seed_oracle_01/analysis.json')==protocol['evidence']['sha256']
    paths=[Path(__file__),D/'residual_query_driver.cpp',D/'src/vpr/src/route/h3d_candidate_path.h',D/'residual_multitarget_query_experiment_01.json',D/'residual_seed_oracle_01/analysis.json',b/'search_domain_analysis.json',b/'input_seal.json',rd/'stdout.log',rd/'manifest.json',graph,D/'verify_path_witnesses_v2.py']
    bound={str(p):sha(p) for p in paths};assert bound[str(graph)]==m['shared_inputs'][str(graph)]['sha256']
    write(out/'registration.json',dict(status='registered_before_execution',native_route_calls=0,source_sha256=bound,protocol=protocol,cpp_query='Exact existing H3dCandidatePath header, stop-at-first-path1, label16384/heap65536/shared256 per arm per seedgroup.',heuristic='Qh min(seedTdel +4*graphunit*Manhattan_lowXY/max(1,mean_planar_span)); ordering only; Q0 zero.',virtual_target='Single virtual target after each actual seed, edge cost saved Tdel, not a physical RR edge.',memory_bytes=24*1024**3,timeout=1800,pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split(') ',1)[1].split()[19]))
    for src in [D/'residual_query_driver.cpp',D/'src/vpr/src/route/h3d_candidate_path.h']:shutil.copy2(src,out/'src'/src.name)
    with (out/'compile.log').open('w') as f:subprocess.run(['g++','-std=c++20','-O2','-Wall','-Wextra','-D_GLIBCXX_ASSERTIONS','-fsanitize=undefined','-fno-sanitize-recover=all','-I',str(out/'src'),str(out/'src/residual_query_driver.cpp'),'-o',str(out/'query')],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
    raw=collections.defaultdict(list);domains={}
    for l in (rd/'stdout.log').read_text().splitlines():
        if l.startswith('H3D_SEARCH_DOMAIN '):r=fields(l);domains[int(r['search'])]=r
        elif l.startswith('H3D_SEARCH_DOMAIN_SEED '):r=fields(l);raw[int(r['search'])].append(dict(node=int(r['node']),delay=float(r['delay_seconds']),layer=int(r['layer'])))
    cases=[]
    for o in oracle['rows']:
        search=o['search'];r=domains[search];assert len(raw[search])==o['seed_pushes'];cases.append(dict(oracle=o,domain=r,seeds=raw[search]))
    write(out/'cases.json',cases)
    with (out/'cases.txt').open('w') as f:
        f.write(str(len(cases))+'\n')
        for c in cases:
            r=c['domain'];f.write(' '.join([r['search'],r['sink']]+[r[k] for k in ['xmin','xmax','ymin','ymax','layer_min','layer_max']]+[str(len(c['seeds']))])+'\n')
            for s in c['seeds']:f.write(f"{s['node']} {s['delay']:.17g}\n")
    nodes=[];switch={};span_sum=0;span_count=0;edgecount=0;started=time.monotonic()
    with (out/'graph.bin').open('wb') as f:
        f.write(b'H3DRQ001'+struct.pack('<IQdd',0,0,0.,0.))
        for section,e in graph_records(graph):
            at=e.attrib
            if section=='switches':
                v=e.find('timing');v={} if v is None else v.attrib;assert all(f32(v.get(k,0))==0 for k in ['R','Cin','Cout','Cinternal']);switch[int(at['id'])]=f32(v.get('Tdel',0))
            elif section=='rr_nodes':
                assert int(at['id'])==len(nodes);v=e.find('loc').attrib;t=e.find('timing');assert t is None or all(float(t.attrib.get(k,0))==0 for k in ['R','C']);layer=int(v.get('layer_low',v.get('layer',0)));assert layer==int(v.get('layer_high',v.get('layer',0)))
                x,y,xh,yh=[int(v[k]) for k in ['xlow','ylow','xhigh','yhigh']];dec=at.get('direction')=='DEC_DIR';nodes.append((x,y,xh if dec else x,yh if dec else y,layer));f.write(struct.pack('<iiiii',*nodes[-1]))
                if at['type'] in ['CHANX','CHANY'] and at.get('direction')!='NONE':span_sum+=xh-x+yh-y+1;span_count+=1
            elif section=='rr_edges':
                u,v,sw=int(at['src_node']),int(at['sink_node']),int(at['switch_id']);f.write(struct.pack('<IId',u,v,switch[sw]));edgecount+=1
        unit=sum(w for w in switch.values() if w>0)/sum(w>0 for w in switch.values());span=span_sum/span_count;f.seek(8);f.write(struct.pack('<IQdd',len(nodes),edgecount,unit,span))
    write(out/'graph_binding.json',dict(source_rrg_sha256=bound[str(graph)],binary_graph_sha256=sha(out/'graph.bin'),nodes=len(nodes),edges=edgecount,unit=unit,mean_span=span,export_seconds=time.monotonic()-started,format='Little-endian magic8/u32nodes/u64edges/f64unit/f64span,20byte nodes(lowXY,driveXY,layer),16byte edges(u32from,u32to,f64Tdel); all zeroRC checked.'))
    with (out/'query_stdout.log').open('w') as f,(out/'query_stderr.log').open('w') as err:subprocess.run([str(out/'query'),str(out/'graph.bin'),str(out/'cases.txt'),'256'],stdout=f,stderr=err,check=True,timeout=600)
    assert all(sha(p)==h for p,h in bound.items());write(out/'execution.json',dict(status='query_execution_terminal_pending_independent_audit',native_route_calls=0,source_sha256=bound,output_sha256={n:sha(out/n) for n in ['query','cases.json','cases.txt','graph_binding.json','query_stdout.log','query_stderr.log']},elapsed_seconds=time.monotonic()-started))
    print('Offline query execution complete; independent path/optimality audit pending',flush=True)
if __name__=='__main__':main()
