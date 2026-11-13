#!/usr/bin/env python3
"""Independent augmented-graph Floyd check, including zero cycles and >2 layers."""
from pathlib import Path
import csv, hashlib, io, json, math, random, struct, subprocess, tempfile
D=Path(__file__).resolve().parent
rng=random.Random(70091);checked=unreachable=zero=0
for case in range(80):
 n=rng.randrange(5,21);layers=[rng.randrange(3) for _ in range(n)]
 edges=[(a,b,rng.choice([0.,.125,.25,.75,1.])) for a in range(n) for b in range(n) if a!=b and rng.random()<.16]
 crossing={a for a,b,w in edges if layers[a]!=layers[b]}
 if not crossing:continue
 truth={}
 for reverse in [0,1]:
  m=2*n;dist=[[math.inf]*m for _ in range(m)]
  for i in range(m):dist[i][i]=0
  for a,b,w in edges:
   if layers[a]==layers[b]:
    u,v=(b,a) if reverse else (a,b);dist[u][v]=min(dist[u][v],w)
   elif reverse:dist[b][n+a]=min(dist[b][n+a],w)
  if not reverse:
   for a in crossing:dist[a][n+a]=0
  for k in range(m):
   for i in range(m):
    if not math.isfinite(dist[i][k]):continue
    for j in range(m):dist[i][j]=min(dist[i][j],dist[i][k]+dist[k][j])
  for a in range(n):
   for c in crossing:truth[a,reverse,c]=dist[a][n+c]
 with tempfile.TemporaryDirectory(prefix='h3d_exact_oracle_') as tmp:
  p=Path(tmp);(p/'layers.bin').write_bytes(b''.join(struct.pack('<i',x) for x in layers));(p/'edges.bin').write_bytes(b''.join(struct.pack('<IIf',*e) for e in edges))
  (p/'requests.txt').write_text(''.join(f'{a} {b} {c}\n' for a,b,c in sorted(truth)))
  run=subprocess.run([str(D/'exact_distances'),str(p),str(p/'requests.txt')],capture_output=True,text=True,check=True,timeout=10)
  rows=list(csv.DictReader(io.StringIO(run.stdout)));assert len(rows)==len(truth)
  for r in rows:
   k=int(r['endpoint']),int(r['reverse']),int(r['target']);actual=float(r['seconds']);expected=truth[k]
   assert actual==expected,(case,k,actual,expected)
   checked+=1;unreachable+=math.isinf(expected);zero+=expected==0
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=dict(passed=True,graphs=80,answers=checked,unreachable=unreachable,zero_distance=zero,scope='Full Dijkstra oracle checked against independently constructed terminal-augmented Floyd graphs. Production exact-cache values will be checked separately on actual RRG trace; not a QoR test.',sha256={p.name:sha(p) for p in [Path(__file__),D/'exact_distances.cpp',D/'exact_distances']})
(D/'oracle_validation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
