#!/usr/bin/env python3
import collections,itertools,math,random,resource,subprocess
from retained_prefix_workflow import D,read,write,sha

def hierarchy(ls):
    if len(ls)<=1:return [tuple([tuple(ls)])]
    xs=[x['x'] for x in ls];ys=[x['y'] for x in ls];sx=max(xs)-min(xs)>=max(ys)-min(ys);order=sorted(ls,key=lambda r:(r['x'] if sx else r['y'],r['pin']));mid=len(ls)//2
    # Every legal hierarchy cut explicitly enumerated; group costs are evaluated afterwards.
    return [tuple([tuple(ls)])]+[a+b for a in hierarchy(order[:mid]) for b in hierarchy(order[mid:])]
def group_cost(group,opening,assignment=None):
    if not group:return 0.
    if assignment is not None:
        if any(l['pin'] not in assignment for l in group):return math.inf
        channels={assignment[l['pin']] for l in group}
        if len(channels)!=1:return math.inf
        c=next(iter(channels))
        if c==len(opening):return group[0]['outside'] if len(group)==1 else math.inf
        return opening[c]+sum(l['candidates'].get(c,math.inf) for l in group) if c<len(opening) else math.inf
    physical=min((opening[c]+sum(l['candidates'].get(c,math.inf) for l in group) for c in range(len(opening))),default=math.inf)
    return min(physical,group[0]['outside']) if len(group)==1 else physical
def oracle(case,independent=False,assignment=None):
    ls=case['leaves'];cuts=[tuple((l,) for l in ls)] if independent else hierarchy(ls)
    return min((sum(group_cost(g,case['opening'],assignment) for g in cut) for cut in cuts),default=0.)
def serialize(cases,path):
    with path.open('w') as f:
        f.write(str(len(cases))+'\n')
        for c in cases:
            f.write(f"{len(c['leaves'])} {len(c['opening'])} {len(c['prior'])}\n");f.write(' '.join(map(str,c['opening']))+'\n')
            for l in c['leaves']:
                out=l['outside'] if math.isfinite(l['outside']) else -1;f.write(' '.join(map(str,[l['pin'],l['x'],l['y'],out,len(l['candidates'])]+[v for k,b in sorted(l['candidates'].items()) for v in [k,b]]))+'\n')
            for p,k in sorted(c['prior'].items()):f.write(f'{p} {k}\n')
def parse(path):
    rows={}
    for line in path.read_text().splitlines():
        v=line.split();assert v[0]=='PLAN';test,mode=int(v[1]),int(v[2]);a=list(map(int,v[8:]));assert len(a)==2*int(v[7]);rows[test,mode]=dict(cost=float(v[3]),previous=float(v[4]),groups=int(v[5]),outside=int(v[6]),assignment=dict(zip(a[::2],a[1::2])))
    return rows
def main():
    resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3));out=D/'outside_dp_core_01';R=D/'src/libs/libvtrutil/src';driver=D/'outside_dp_driver.cpp'
    with (out/'compile.log').open('w') as f:subprocess.run(['g++','-std=c++20','-O2','-D_GLIBCXX_ASSERTIONS','-fsanitize=undefined','-fno-sanitize-recover=all','-I',str(out/'src'),'-I',str(R),str(driver),str(R/'vtr_assert.cpp'),'-o',str(out/'driver')],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=120)
    rng=random.Random(542781);cases=[];pairs=[]
    for trial in range(320):
        n=rng.randrange(1,8);m=rng.randrange(0,5);opening=[float(rng.randrange(16)) for _ in range(m)];leaves=[];prior={}
        for pin in range(1,n+1):
            cs={c:float(rng.randrange(20)) for c in range(m) if rng.random()<.7};outside=float(rng.randrange(28)) if rng.random()<.65 else math.inf;leaves.append(dict(pin=pin,x=rng.randrange(6),y=rng.randrange(6),outside=outside,candidates=cs));
            if rng.random()<.8:prior[pin]=rng.randrange(m+2)
        cases.append(dict(opening=opening,leaves=leaves,prior=prior))
        no=[dict(l,outside=math.inf) for l in leaves];zero=[dict(l,outside=max(l['outside'],min((opening[c]+b for c,b in l['candidates'].items()),default=math.inf))) for l in leaves]
        first=len(cases);cases.extend([dict(opening=opening,leaves=no,prior=prior),dict(opening=opening,leaves=zero,prior=prior)]);pairs.append((first,first+1))
    serialize(cases,out/'unit_cases.txt')
    with (out/'unit_results.log').open('w') as f,(out/'unit_stderr.log').open('w') as err:subprocess.run([str(out/'driver')],stdin=(out/'unit_cases.txt').open(),stdout=f,stderr=err,check=True,timeout=120)
    rows=parse(out/'unit_results.log');checked=0;outside=0
    for (index,mode),r in rows.items():
        c=cases[index];expected=oracle(c,mode);old=oracle(c,mode,c['prior']);assert r['cost']==expected and r['previous']==old,(index,mode,r,expected,old)
        if math.isfinite(expected):
            assert oracle(c,mode,r['assignment'])==expected;assert len(r['assignment'])==len(c['leaves']);assert r['outside']==sum(a==len(c['opening']) for a in r['assignment'].values());outside+=r['outside']
        checked+=1
    for a,b in pairs:
        for mode in [0,1]:assert rows[a,mode]['cost']==rows[b,mode]['cost'] and rows[a,mode]['assignment']==rows[b,mode]['assignment'] and rows[b,mode]['outside']==0
    write(out/'unit_validation.json',dict(passed=True,plans_checked=checked,random_tables=320,eta0_pairs=len(pairs)*2,outside_selected_total=outside,source_sha256={str(p):sha(p) for p in [__file__,driver,out/'src/h3d_partition_dp.h',out/'src/h3d_independent_plan.h',out/'driver']},qualification='Independent exhaustive enumeration of all cuts of the deterministic hierarchy, with group feasibility/cost evaluated directly, shared and independent optima and fixed prior assignment costs. Missing/invalid/only-outside/zero-cost/tie cases, eta0 exact assignment preservation, UBSan and std assertions. Not native integration or QoR evidence.'))
    print('outside DP core unit passed',checked,'eta0_pairs',len(pairs)*2,'outside',outside)
if __name__=='__main__':main()
