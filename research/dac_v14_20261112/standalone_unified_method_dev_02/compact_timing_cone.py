"""Compact setup-cone reader. Selection evidence, never a physical/STA audit."""
import array,collections,hashlib,math
from pathlib import Path
import numpy as np
from current_sta_arrival_cone import f32

def read_compact(path,launches,endpoints):
 kinds=[];offsets=[0];incoming=array.array('i');src=array.array('i');dst=array.array('i');disabled=bytearray();delay=array.array('d')
 arrivals={l:{} for l in launches};slacks={};section=None;sections=[];node=edge=-1;constraints=[];delays_seen=0
 for raw in Path(path).open():
  line=raw.strip().removesuffix('\\').strip()
  if not line:continue
  if line in ['timing_graph:','timing_constraints:','delay_model:','analysis_result:']:
   section=line[:-1];sections.append(section);continue
  assert section is not None
  if section=='timing_graph':
   key,value=line.split(':',1);value=value.strip()
   if key=='node':
    node=int(value);assert node==len(kinds);kinds.append(None)
   elif key=='edge':
    edge=int(value);assert edge==len(src);src.append(-1);dst.append(-1);disabled.append(2);delay.append(math.nan)
   elif edge<0:
    if key=='type':assert kinds[node] is None;kinds[node]=value
    elif key=='in_edges':
     assert len(offsets)==node+1;incoming.extend(map(int,value.split()));offsets.append(len(incoming))
    else:assert key=='out_edges' # Not consumed by backward selection.
   else:
    if key=='src_node':src[edge]=int(value)
    elif key=='sink_node':dst[edge]=int(value)
    elif key=='disabled':assert value in ['true','false'];disabled[edge]=int(value=='true')
    else:assert key=='type'
  elif section=='timing_constraints':constraints.append(line)
  elif section=='delay_model':
   v=line.split();assert len(v)==6 and v[0]=='edge:';idx=int(v[1]);assert idx==delays_seen;delays_seen+=1
   assert (v[2],v[4]) in [('min_delay:','max_delay:'),('setup_time:','hold_time:')]
   if v[4]=='max_delay:':delay[idx]=float(v[5]);assert math.isfinite(delay[idx])
  else:
   if line.startswith('type: SETUP_DATA_ARRIVAL node:') or line.startswith('type: SETUP_SLACK node:'):
    v=line.split();assert len(v)==10 and v[4]=='launch_domain:' and v[6]=='capture_domain:'
    typ,n,l,c,value=v[1],int(v[3]),int(v[5]),int(v[7]),float(v[9])
    if typ=='SETUP_DATA_ARRIVAL' and l in launches and c==-1:
     assert v[8]=='time:'
     if n in arrivals[l]:assert arrivals[l][n]==value
     arrivals[l][n]=value
    elif typ=='SETUP_SLACK' and (n,l,c) in endpoints:
     assert v[8]=='slack:'
     if (n,l,c) in slacks:assert slacks[n,l,c]==value
     slacks[n,l,c]=value
 assert sections==['timing_graph','timing_constraints','delay_model','analysis_result']
 n,m=len(kinds),len(src);assert n and m and all(kinds) and len(offsets)==n+1 and delays_seen==m
 assert len(incoming)==m and all(d in [0,1] for d in disabled)
 ss=np.frombuffer(src,dtype=np.int32);dd=np.frombuffer(dst,dtype=np.int32);ii=np.frombuffer(incoming,dtype=np.int32)
 assert ss.min()>=0 and ss.max()<n and dd.min()>=0 and dd.max()<n and ii.min()>=0 and ii.max()<m
 assert np.all(np.bincount(ii,minlength=m)==1)
 assert np.array_equal(dd[ii],np.repeat(np.arange(n),np.diff(offsets)))
 assert set(slacks)==set(endpoints)
 return dict(kinds=kinds,offsets=offsets,incoming=incoming,src=src,dst=dst,disabled=disabled,delay=delay,arrivals=arrivals,slacks=slacks,
  constraints_text_sha256=hashlib.sha256('\n'.join(constraints).encode()).hexdigest(),scope='Only setup selection fields; complete native FULL/STA and independent legality audits remain separate.')

def trace_compact(g,roots,launch):
 arrivals=g['arrivals'][launch];seen=set();selected=set();sources=[];unresolved=[];fanins=[];todo=list(roots)
 while todo:
  node=todo.pop()
  if node in seen:continue
  seen.add(node)
  if node not in arrivals:unresolved.append(dict(node=node,reason='missing matching arrival domain'));continue
  if g['kinds'][node]=='SOURCE':sources.append(node);continue
  choices=[]
  for pos in range(g['offsets'][node],g['offsets'][node+1]):
   e=g['incoming'][pos];source=g['src'][e];delay=g['delay'][e]
   if g['disabled'][e] or source not in arrivals or math.isnan(delay):continue
   proposal=f32(arrivals[source]+delay);choices.append(dict(edge=e,source=source,proposal_s=proposal,gap_s=arrivals[node]-proposal))
  if not choices or max(p['proposal_s'] for p in choices)!=arrivals[node]:
   unresolved.append(dict(node=node,reason='native maximum recurrence not reproduced'));continue
  wins=[p for p in choices if p['proposal_s']==arrivals[node]]
  fanins.append(dict(node=node,arrival_s=arrivals[node],choices=choices,winning_edges=[p['edge'] for p in wins]))
  for p in wins:selected.add(p['edge']);todo.append(p['source'])
 return dict(nodes=sorted(seen),edges=sorted(selected),sources=sorted(sources),unresolved=unresolved,fanins=fanins)
