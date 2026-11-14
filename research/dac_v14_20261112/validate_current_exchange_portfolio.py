#!/usr/bin/env python3
"""Check generic dependency-closure request construction against the native control."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from current_proposal_portfolio import request_text
p=D/'current_exchange_portfolio_Tf_01/portfolio.json';x=read(p);assert x['passed'] and len(x['proposals'])==1
item=x['proposals'][0];plan=read(item['plan']);reg=read(D/'critical_owner_exchange_dev_01/registration.json');old=reg['roles']['000_expanded_free_weighted'];assert plan['source_state']==old['state'];assert request_text(plan)==Path(old['request']).read_text();assert item['request_sha256']==sha(old['request'])
assert not old['fixed_target_paths'] and len(plan['repair_pins'])==13
out=D/'current_exchange_portfolio_validation_01.json';assert not out.exists();write(out,dict(passed=True,requests_equal=True,repair_connections=13,no_fixed_target_paths=True,native_calls=0,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),D/'make_current_exchange_portfolio.py',D/'current_proposal_portfolio.py',p,Path(item['plan']),D/'critical_owner_exchange_dev_01/registration.json',Path(old['request'])]},qualification='Generic current-state free native request is byte-identical to the registered equal-opportunity control. Does not assert a different search kernel or final general algorithm performance.'))
print('Generic free exchange request matches the native control')
