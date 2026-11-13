#!/usr/bin/env python3
import math,random,struct,subprocess,collections
from retained_prefix_workflow import D,read,write,sha
from audit_residual_query_offline import parse,near

def main():
    b=D/'residual_query_offline_01';out=D/'residual_query_adapter_unit_01';out.mkdir(exist_ok=False);rng=random.Random(143923);nodes=[];edges=[];cases=[];expected={}
    # Independent Floyd on random small directed graphs, then convert to the same binary adapter input.
    for g in range(180):
        start=len(nodes);n=8;sink=start+rng.randrange(n);base=g*20;part=[]
        for i in range(n):
            x=base+rng.randrange(8);y=rng.randrange(8);part.append((x,y,x+rng.randrange(2),y,rng.randrange(2)))
        nodes.extend(part);xmin=base+rng.randrange(3);xmax=base+6;ymin=0;ymax=7;xmin=min(xmin,nodes[sink][2]);xmax=max(xmax,nodes[sink][2]);bbox=(xmin,xmax,ymin,ymax,0,1)
        def inside(i):return xmin<=nodes[i][2]<=xmax and ymin<=nodes[i][3]<=ymax
        layer=nodes[sink][4];d=[[math.inf]*n for _ in range(n)]
        for i in range(n):d[i][i]=0
        for i in range(n):
            for j in range(n):
                if rng.random()<.28:
                    w=rng.choice([0.,0.,1.,2.,5.]);edges.append((start+i,start+j,w))
                    if nodes[start+i][4]==nodes[start+j][4]==layer and inside(start+i) and inside(start+j):d[i][j]=min(d[i][j],w)
        for k in range(n):
            for i in range(n):
                for j in range(n):d[i][j]=min(d[i][j],d[i][k]+d[k][j])
        seeds=[(start+rng.randrange(n),rng.choice([0.,1.,3.,7.])) for _ in range(rng.randrange(10))]
        if g%7==0:seeds.append((sink,0.))
        cost=min((t+d[u-start][sink-start] for u,t in seeds if nodes[u][4]==layer and (inside(u) or u==sink)),default=math.inf)
        cases.append((g,sink,bbox,seeds));expected[g]=cost
    # A degree exceeding the shared storage cap must report MEMORY_LIMIT without false lower certification.
    start=len(nodes);nodes.extend([(5000,0,5000,0,0)]*24002);sink=start;seeds=[(start+24001,2.)];edges.extend((start+i,sink,1.) for i in range(1,24002));cases.append((180,sink,(4999,5001,0,1,0,0),seeds));expected[180]=3.
    with (out/'graph.bin').open('wb') as f:
        f.write(b'H3DRQ001'+struct.pack('<IQdd',len(nodes),len(edges),1.,2.))
        for node in nodes:f.write(struct.pack('<iiiii',*node))
        for e in edges:f.write(struct.pack('<IId',*e))
    with (out/'cases.txt').open('w') as f:
        f.write(str(len(cases))+'\n')
        for search,sink,bb,seeds in cases:
            f.write(' '.join(map(str,[search,sink,*bb,len(seeds)]))+'\n')
            for u,t in seeds:f.write(f'{u} {t}\n')
    checked=0;stops=collections.Counter()
    for budget in [0,1,256]:
        p=out/f'budget_{budget}.log'
        with p.open('w') as f,(out/f'budget_{budget}.stderr').open('w') as err:subprocess.run([str(b/'query'),str(out/'graph.bin'),str(out/'cases.txt'),str(budget)],stdout=f,stderr=err,check=True,timeout=60)
        rows,paths=parse(p)
        for key,r in rows.items():
            checked+=1;opt=expected[key[0]];stops[r['stop']]+=1;path=paths[key];assert r['expansions']<=budget
            if r['upper_seconds'] is not None:
                assert math.isfinite(opt) and r['upper_seconds']>=opt and near(sum(x[2] for x in path),r['upper_seconds']);assert path[0][0]==cases[key[0]][1] and path[-1][1]==len(nodes)
                for u,v,w,toll in path[:-1]:assert (v,u,w) in edges and toll==0
                assert path[-1][:1][0] in [u for u,t in cases[key[0]][3]]
            if r['lower_seconds'] is not None:assert r['lower_seconds']<=opt
            if r['stop']==0:assert near(r['upper_seconds'],opt)
            if r['stop']==2:assert math.isinf(opt)
            if budget==256 and key[0]<180 and key[1]==0:assert r['stop']==(0 if math.isfinite(opt) else 2)
            if budget==256 and key[0]==180:assert r['stop']==4 and r['lower_seconds'] is None
    write(out/'validation.json',dict(passed=True,adapter_results_checked=checked,random_graphs=180,dense_storage_case=True,stop_counts=dict(stops),source_sha256={str(p):sha(p) for p in [__file__,b/'query',b/'src/h3d_candidate_path.h',b/'src/residual_query_driver.cpp']},qualification='Independent Floyd optima on random directed zero-cycle graphs with layer/BB filtering and multiple weighted targets; source==seed, no-seed, work0/1/256 and actual16384-label storage stop. Exact/bound/path and virtual-prefix validity tested; no full FPGA legal-extension claim.'))
    print('adapter unit passed',checked,dict(stops))
if __name__=='__main__':main()
