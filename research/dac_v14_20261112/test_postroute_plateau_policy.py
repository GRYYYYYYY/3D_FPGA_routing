from copy import deepcopy
from postroute_plateau_policy import decide

base=dict(native_valid=True,zero_rc_verified=True,before_cpd=6.,after_cpd=6.,
    before_sta=dict(sWNS=-6.,sTNS=-100.,hWNS=0.,hTNS=0.),after_sta=dict(sWNS=-6.,sTNS=-100.,hWNS=0.,hTNS=0.),
    physical=dict(passed=True,other_net_traces_exact=True,sink_connections=20,changed=[dict(before_ns=2.,after_ns=1.)]),
    route_hash='new',seen_hashes=['old'])
assert decide(**base)['accepted']
cases=[]
for name in ['native_valid','zero_rc_verified']:
    c=deepcopy(base);c[name]=False;cases.append(c)
for name in ['sWNS','sTNS','hWNS','hTNS']:
    c=deepcopy(base);c['after_sta'][name]-=1.;cases.append(c)
c=deepcopy(base);c['after_cpd']=7.;cases.append(c)
c=deepcopy(base);c['after_cpd']=float('nan');cases.append(c)
c=deepcopy(base);del c['after_sta']['sTNS'];cases.append(c)
c=deepcopy(base);c['route_hash']='old';cases.append(c)
c=deepcopy(base);c['physical']['changed']=[];cases.append(c)
c=deepcopy(base);c['physical']['changed'][0]['after_ns']=3.;cases.append(c)
c=deepcopy(base);c['physical']['changed'].append(dict(before_ns=3.,after_ns=4.));cases.append(c)
c=deepcopy(base);c['physical']['sink_connections']=0;cases.append(c)
assert all(not decide(**c)['accepted'] for c in cases)
print('PASS plateau acceptance and14 invalid/nonmonotone/incomplete/repeated-state controls')
