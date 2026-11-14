#!/usr/bin/env python3
"""Compare cached physical audits with sealed XML audits; no route/STA runs."""
import argparse, json, os, resource, shutil, signal, subprocess, sys, tempfile, time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from immutable_rr_audit_cache import GraphAuditCache

def main():
    p=argparse.ArgumentParser();p.add_argument('--batch',type=Path,required=True);p.add_argument('--cache',type=Path,required=True);a=p.parse_args()
    started=time.monotonic();b=a.batch.resolve();b.mkdir(exist_ok=False);cache=a.cache.resolve()
    resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));assert shutil.disk_usage(D).free>=80*1024**3
    cases=['current_sta_policy_native_Tf_01/attempt_001','current_sta_policy_native_R1_01/attempt_004']
    inputs=[Path(__file__).resolve(),D/'immutable_rr_audit_cache.py',D/'audit_native_objective_cached.py',D/'audit_native_objective.py',D/'current_sta_state_reuse_experiment_01.json',cache/'completion.json']
    inputs += [D/c/'candidate_audit/analysis.json' for c in cases]
    bindings={str(p):sha(p) for p in inputs}
    write(b/'registration.json',dict(status='registered_before_work',source_sha256=bindings,cases=cases,question='Does actual-XML-bound cache preserve complete candidate reconstruction, scope, switch and capacity checks on accepted and rejected candidates?',native_calls=0,guards=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3)))
    results=[]
    for i,name in enumerate(cases):
        target=b/f'audit_{i:02d}';command=[sys.executable,str(D/'audit_native_objective_cached.py'),'--batch',str(D/name),'--role','candidate','--cache',str(cache),'--output',str(target)]
        t=time.monotonic()
        with (b/f'audit_{i:02d}.log').open('w') as f:
            process=subprocess.Popen(command,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
            try:code=process.wait(timeout=1800)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL);process.wait();raise
        elapsed=time.monotonic()-t
        assert code==0,(name,code)
        ref=read(D/name/'candidate_audit/analysis.json');actual=read(target/'analysis.json')
        keys=['passed','status','scope','queries','attempts','changed_delays','native_transaction_seconds']
        assert all(ref[k]==actual[k] for k in keys),name
        assert sha(ref['candidate_route'])==sha(actual['candidate_route']),name
        results.append(dict(case=name,equivalent_fields=keys,complete_candidate_bytes_equal=True,candidate_sha256=sha(actual['candidate_route']),cached_audit_segment_seconds=actual['audit_and_serialization_seconds'],cache_load_and_digest_seconds=actual['graph_cache']['load_and_digest_seconds'],cached_complete_process_seconds=elapsed,historical_XML_audit_segment_seconds=ref['audit_and_serialization_seconds'],timing_qualification='Historical XML segment is context, not a same-time formal paired speedup; cached child includes process startup and output writes.'))
        bindings[str(target/'analysis.json')]=sha(target/'analysis.json')
        write(b/'progress.json',results)
    graph=Path(read(cache/'completion.json')['graph']);g=GraphAuditCache(graph,cache)
    rejected=[]
    def must_reject(label,fn):
        try:fn()
        except AssertionError:rejected.append(label)
        else:raise AssertionError('Invalid input accepted: '+label)
    first=int(g.edges[0]);sid=first%g.stride;uv=first//g.stride;u,v=divmod(uv,g.n)
    g.require_edges([(u,v,sid)])
    missing=None
    import numpy as np
    for node in range(32):
        key=(node*g.n+node)*g.stride+sid;pos=int(np.searchsorted(g.edges,np.uint64(key)))
        if pos==len(g.edges) or int(g.edges[pos])!=key:missing=(node,node,sid);break
    assert missing is not None
    must_reject('nonexistent_in_range_edge',lambda:g.require_edges([missing]))
    must_reject('invalid_switch',lambda:g.require_edges([(u,v,g.stride)]))
    must_reject('invalid_node',lambda:g.metadata({g.n}))
    g.require_occupancy({u:int(g.capacities[u])})
    must_reject('over_capacity_by_one',lambda:g.require_occupancy({u:int(g.capacities[u])+1}))
    with tempfile.TemporaryDirectory(dir=b) as temp:
        temp=Path(temp);wrong=temp/'wrong.xml';wrong.write_text('<rr_graph/>')
        must_reject('different_actual_XML_digest',lambda:GraphAuditCache(wrong,cache))
        bad=temp/'bad_cache';bad.mkdir()
        c=read(cache/'completion.json');c['payload_sha256']['edges.npy']='0'*64
        write(bad/'completion.json',c)
        for name in ['nodes.npy','edges.npy','switches.npy']:(bad/name).symlink_to(cache/name)
        must_reject('payload_digest_mismatch',lambda:GraphAuditCache(graph,bad))
    assert all(sha(path)==digest for path,digest in bindings.items())
    write(b/'completion.json',dict(passed=True,case_results=results,negative_controls_rejected=rejected,positive_edge_and_exact_capacity_controls=True,source_sha256=bindings,complete_validation_seconds=time.monotonic()-started,cache_build_seconds=read(cache/'completion.json')['complete_build_seconds'],native_calls=0,qualification='Physical graph-cache engineering validation on existing candidates, not new QoR or STA evidence. No original XML audit weakened or overwritten. Cache reuse still hashes actual XML and every payload.'))
    print(dict(passed=True,complete_child_seconds=[r['cached_complete_process_seconds'] for r in results],negative_controls=len(rejected)),flush=True)

if __name__=='__main__':main()
