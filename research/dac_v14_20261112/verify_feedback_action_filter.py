"""Check actual proposal/action logs against the registered ablation policy."""
from pathlib import Path
import re,json

def verify(rd,policy):
 rd=Path(rd);events=[];main=[]
 assert policy in ['clear','reassign','finite','incomplete']
 for line in (rd/'stdout.log').read_text().splitlines():
  if line.startswith('H3D_REFRESH_ACTION '):
   fields=dict(re.findall(r'(\w+)=([^ ]+)',line));assert fields['policy']==policy
   clear=fields['clear']=='1'
   allowed=clear if policy=='clear' else not clear
   if policy in ['finite','incomplete']:allowed=allowed and ((fields['prior_finite']=='1')==(policy=='finite'))
   assert (fields['accepted']=='1')==((fields['proposed_accepted']=='1') and allowed)
   events.append(fields)
  if line.startswith('H3D_REFRESH '):main.append(dict(re.findall(r'(\w+)=([^ ]+)',line)))
 assert events and len(events)==len(main)
 assert all(all(a[k]==b[k] for k in ['net','iter','accepted']) for a,b in zip(events,main))
 result=dict(passed=True,policy=policy,attempts=len(events),proposals_accepted=sum(x['proposed_accepted']=='1' for x in events),accepted=sum(x['accepted']=='1' for x in events),rejected_by_action=sum(x['proposed_accepted']=='1' and x['accepted']=='0' for x in events))
 (rd/'action_filter_check.json').write_text(json.dumps(result,indent=2)+'\n');return result
