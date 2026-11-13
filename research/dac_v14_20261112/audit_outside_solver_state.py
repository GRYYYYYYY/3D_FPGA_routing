#!/usr/bin/env python3
import argparse,collections,math,subprocess,sys
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from verify_path_witnesses_v2 import fields
from test_outside_dp_core import serialize,parse
from audit_residual_query_offline import near
ROOT=D.parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from check_route import read_trace

def digest(size,paths):
    h=14695981039346656037
    def mix(v):
        nonlocal h
        for i in range(8):h=((h^(v&255))*1099511628211)&((1<<64)-1);v>>=8
    mix(size)
    for pin in range(size):
        p=paths.get(pin,());mix(bool(p));mix(len(p))
        for n in p:mix(n)
    return h

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--arm',required=True);ap.add_argument('--batch',default='outside_native_eltwise_dev_02');args=ap.parse_args();b=D/args.batch;rd=b/'runs'/('eltwise_layer_'+args.arm);assert read(b/'input_seal.json')['passed'];assert read(rd/'manifest.json')['status']=='completed'
    local=read(b/('outside_tree_'+args.arm+'.json'));assert local['passed'];core=D/'outside_dp_core_01';stage=D/'outside_native_stage_01';assert all(sha(stage/'src/vpr/src/route'/n)==sha(core/'src'/n) for n in ['h3d_partition_dp.h','h3d_independent_plan.h'])
    base=D/'outside_native_eltwise_dev_01/runs/eltwise_layer_C2';routes=read_trace(base/'routed.route');sizes={n:max(x.pin for x in v['trace'] if x.pin is not None)+1 for n,v in routes.items()};coords={(n,x.pin):x.low[:2] for n,v in routes.items() for x in v['trace'] if x.kind=='SINK' and x.pin is not None}
    contexts={};leaflog={};prefix_event={};entries=collections.defaultdict(dict);pairs=collections.defaultdict(dict);decisions={};costs={};solvers={};assignments=collections.defaultdict(dict);best_raw={};valid_paths=collections.defaultdict(list);path_rows=collections.defaultdict(list);event=None
    state=collections.defaultdict(dict);prior_state={};backup={};save={};save_checks=0;final_state={};final_paths=collections.defaultdict(dict);rejects=[];rollbacks=[]
    for w in local['rows']:
        if w['reason']=='valid':best_raw[w['event'],w['pin']]=min(best_raw.get((w['event'],w['pin']),math.inf),w['raw'])
    for line in (rd/'stdout.log').read_text().splitlines():
        if line.startswith('H3D_TARGET_REFRESH '):r=fields(line);backup[int(r['net'])]=dict(state[int(r['net'])])
        elif line.startswith('H3D_OUTSIDE_CONTEXT '):r=fields(line);event=int(r['event']);contexts[event]=r;prior_state[event]=dict(state[int(r['net'])])
        elif line.startswith('H3D_OUTSIDE_LEAF '):r=fields(line);leaflog[int(r['event']),int(r['pin'])]=r
        elif line.startswith('H3D_OUTSIDE_EDGE '):r=fields(line);path_rows[int(r['event']),int(r['pin']),int(r['witness'])].append(r)
        elif line.startswith('H3D_OUTSIDE_WITNESS '):
            r=fields(line)
            if r['reason']=='valid':
                es=path_rows[int(r['event']),int(r['pin']),int(r['witness'])];path=(int(r['anchor']),)+tuple(int(e['from']) for e in reversed(es));valid_paths[int(r['event']),int(r['pin'])].append((float(r['raw']),path))
        elif line.startswith('H3D_OUTSIDE_COST '):r=fields(line);costs[int(r['event']),int(r['pin'])]=r
        elif line.startswith('H3D_OUTSIDE_SOLVER '):r=fields(line);solvers[int(r['event'])]=r
        elif line.startswith('H3D_PREFIX_TABLE '):
            r=fields(line)
            if event is not None and r['net']==contexts[event]['net']:prefix_event[int(r['plan'])]=event
        elif line.startswith('H3D_PREFIX_ENTRY '):
            r=fields(line);p=int(r['plan'])
            if p in prefix_event:entries[p][int(r['entry'])]=float(r['opening_units'])
        elif line.startswith('H3D_PREFIX_PAIR '):
            r=fields(line);p=int(r['plan'])
            if p in prefix_event:pairs[p][int(r['pin']),int(r['entry'])]=r
        elif line.startswith('H3D_PREFIX_DECISION '):r=fields(line);decisions[int(r['plan'])]=r
        elif line.startswith('H3D_OUTSIDE_ASSIGN '):
            r=fields(line);ev,net,pin=int(r['event']),int(r['net']),int(r['pin']);assignments[ev][pin]=r
            if r['kind']=='outside':
                path=tuple(map(int,r['path'].split(',')));assert int(r['resource'])==-1 and any(p==path and near(cost,best_raw[ev,pin]) for cost,p in valid_paths[ev,pin]);state[net][pin]=path
            else:assert r['kind']=='physical' and int(r['resource'])>=0 and r['path']=='-';state[net].pop(pin,None)
        elif line.startswith('H3D_OUTSIDE_TEST_REJECT '):
            r=fields(line);n=int(r['net']);assert int(r['before'])==digest(sizes[n],backup[n]) and int(r['current'])==digest(sizes[n],state[n]);rejects.append(r)
        elif line.startswith('H3D_GUIDE_ROLLBACK '):
            r=fields(line);n=int(r['net']);state[n]=dict(backup.get(n,{}))
        elif line.startswith('H3D_OUTSIDE_ROLLBACK '):
            r=fields(line);n=int(r['net']);assert int(r['expected'])==int(r['restored'])==digest(sizes[n],state[n]);rollbacks.append(r)
        elif line.startswith('H3D_OUTSIDE_SAVE '):
            r=fields(line);n=int(r['net']);assert int(r['digest'])==digest(sizes[n],state[n]),('save_digest',n,r,state[n]);save[n]=(int(r['digest']),dict(state[n]));save_checks+=1
        elif line.startswith('H3D_FINAL_OUTSIDE_STATE '):r=fields(line);final_state[int(r['net'])]=int(r['digest'])
        elif line.startswith('H3D_FINAL_OUTSIDE '):r=fields(line);final_paths[int(r['net'])][int(r['pin'])]=tuple(map(int,r['path'].split(',')))
    for n,d in final_state.items():assert n in save and d==save[n][0]==digest(sizes[n],final_paths[n]) and final_paths[n]==save[n][1],('final_metadata',n)
    cases=[];plans=[];metadata=[];eta=float(read(rd/'manifest.json')['environment']['VPR_H3D_OUTSIDE_ETA'])
    for p,ev in sorted(prefix_event.items()):
        assert ev in solvers;ctx=contexts[ev];opening=list(entries[p].values());indices={n:i for i,n in enumerate(entries[p])};pins=sorted({pin for pin,e in pairs[p]});leaves=[];prior={}
        for pin in pins:
            rs=[r for (q,e),r in pairs[p].items() if q==pin];candidates={indices[int(r['entry'])]:float(r['branch_units']) for r in rs};raw=best_raw.get((ev,pin),math.inf);standalone=min((opening[i]+v for i,v in candidates.items()),default=math.inf);outside=max(raw,(1.-eta)*standalone);cost=costs[ev,pin]
            assert near(raw,float(cost['raw'])) and near(standalone,float(cost['standalone'])) and near(outside,float(cost['outside'])) and eta==float(cost['eta'])
            x,y=coords[int(ctx['net']),pin];leaves.append(dict(pin=pin,x=x,y=y,candidates=candidates,outside=outside))
            old=[indices[int(r['entry'])] for r in rs if r['prior']=='1']
            if pin in prior_state[ev]:prior[pin]=len(opening)
            elif len(old)==1:prior[pin]=old[0]
        cases.append(dict(opening=opening,leaves=leaves,prior=prior));plans.append(p);metadata.append(ev)
    out=b/('solver_state_'+args.arm);out.mkdir(exist_ok=False);serialize(cases,out/'cases.txt')
    with (out/'results.log').open('w') as f,(out/'stderr.log').open('w') as e:subprocess.run([str(core/'driver')],stdin=(out/'cases.txt').open(),stdout=f,stderr=e,check=True,timeout=120)
    results=parse(out/'results.log');reports=[]
    for i,(p,ev) in enumerate(zip(plans,metadata)):
        result=results[i,0];decision=decisions[p];solver=solvers[ev];assert near(result['cost'],float(decision['new_cost'])) and near(result['previous'],float(decision['old_cost'])),('dp_cost',p,ev,result,decision)
        assert near(result['cost'],float(solver['cost'])) and result['groups']==int(solver['groups']) and result['outside']==int(solver['outside']);accept=math.isfinite(result['cost']) and (not math.isfinite(result['previous']) or result['cost']<.95*result['previous']);assert accept==bool(int(decision['accepted']))
        if accept:
            expected={pin:('outside',-1) if idx==len(cases[i]['opening']) else ('physical',list(entries[p])[idx]) for pin,idx in result['assignment'].items()};actual={pin:(r['kind'],int(r['resource'])) for pin,r in assignments[ev].items()};assert expected==actual,('assignment',ev,expected,actual)
        else:assert not assignments[ev]
        reports.append(dict(plan=p,event=ev,cost=result['cost'],prior_cost=result['previous'],groups=result['groups'],outside=result['outside'],accepted=accept,assignment=result['assignment']))
    summary=dict(refresh_tables=len(reports),outside_leaf_proposals=sum(r['outside'] for r in reports),accepted_outside_leafs=sum(r['outside'] for r in reports if r['accepted']),outside_accepted_plans=sum(r['outside']>0 and r['accepted'] for r in reports),prior_outside_leaf_events=sum(len(v) for v in prior_state.values()),save_digest_checks=save_checks,final_digest_checks=len(final_state),final_outside_leaves=sum(map(len,final_paths.values())),forced_rejections=len(rejects),outside_rollback_checks=len(rollbacks))
    binding={str(p):sha(p) for p in [Path(__file__),b/('outside_tree_'+args.arm+'.json'),rd/'stdout.log',rd/'manifest.json',base/'routed.route',core/'driver',core/'unit_validation.json',out/'cases.txt',out/'results.log']};write(b/('outside_solver_state_'+args.arm+'.json'),dict(passed=True,status='sealed_native_outside_extended_DP_and_state',summary=summary,rows=reports,rejects=rejects,rollback_records=rollbacks,source_sha256=binding,qualification='All finite refresh costs and physical/outside prior kinds reconstructed from actual accepted choice history and prefix matrices, solved with independently exhaustive-tested exact same native solver headers; raw outside options separately graph/tree/current-price checked. 5% acceptance and emitted assignments verified. Outside vectors reconstructed from accepted assignments; per-net full vector-size/flag/path digests checked at every best save and against final restored descriptor. Zero-eligible clears after outside state must be explicitly examined if observed; this checker fails unaccounted state changes. Forced rollback metadata checked where applicable, native complete-tree/feedback restoration remains original VPR transaction with independent final route audit. No CPD gain inferred from fewer guides.'))
    print(summary)
if __name__=='__main__':main()
