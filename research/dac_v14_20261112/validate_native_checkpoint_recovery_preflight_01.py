from pathlib import Path
from types import SimpleNamespace
import sys
r=Path('research/dac_v14_20261112').resolve();sys.path.insert(0,str(r))
from retained_prefix_workflow import read,write,sha
from resource_checkpoint_recovery_v1 import Recovery
class BeforeNativeLoad(Exception):pass
class StopPool:
 def analyze(self,*args,**kwargs):raise BeforeNativeLoad()
out=r/'native_checkpoint_recovery_preflight_01';out.mkdir(exist_ok=False);results=[]
for name,old in [('R1',r/'stable_seed_transfer_dev_01/bnn_R1_native'),('Tf',r/'stable_seed_transfer_recovery_01/bnn_Tf_native')]:
 reg=read(old/'registration.json');b=out/name;b.mkdir()
 args=SimpleNamespace(domain_mode='unrestricted',domain_feedback=False,initial_state=Path(reg['initial_state']),bundle_size=reg['bundle_size'],seed_order=reg['seed_order'],graph_echo=reg['graph_echo'],accepted_steps=reg['local_probe']['accepted_steps'],rank_windows=reg['local_probe']['ranked_candidates_per_state'])
 recovery=Recovery(old,args,b)
 ranks=[0,1] if name=='R1' else [0]
 for rank in ranks:
  tx=old/f'round_{len(recovery.steps):03d}'/f'candidate_{rank:02d}'
  try:recovery.consume(len(recovery.steps),rank,'reuse_off',recovery.state,tx/'request.txt',tx/'domain.txt',SimpleNamespace(pool=StopPool()),b/f'candidate_{rank:02d}',reg['anchor'])
  except BeforeNativeLoad:results.append(dict(case=name,rank=rank,all_pre_LOAD_identity_and_artifact_checks_passed=True))
  else:raise AssertionError('Expected fresh native LOAD gate')
 for f in recovery.locks:f.close()
write(out/'completion.json',dict(passed=True,checks=results,native_calls=0,source_sha256={str(p):sha(p) for p in [r/'resource_checkpoint_recovery_v1.py',r/'run_seed_census_checkpoint_recovery_v1.py']},qualification='Actual original checkpoint and completed worker input/artifact/domain/topology proofs validated up to fresh native LOAD. Does not prove fresh STA equivalence, candidate policy replay, recovered trajectory, or final seal.'))
print(results,flush=True)
