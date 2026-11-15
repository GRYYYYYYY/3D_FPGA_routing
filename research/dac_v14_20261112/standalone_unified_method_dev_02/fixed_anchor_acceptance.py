"""Separate immutable design budgets from current-state transition progress."""
import math
from endpoint_timing_policy import decide as timing_decide
from multiobjective_acceptance_v2 import decide as budget_decide

def decisions(before,after,current_resources,new_resources,anchor,native_valid=True,transaction_complete=True):
 result={n:timing_decide(n,before,after,native_valid and transaction_complete) for n in ['strict','endpoint_vector']}
 for mode in ['timing_under_resources','resources_under_timing']:
  caps=dict(wirelength=math.ceil(anchor['wirelength']*(1.05 if mode=='timing_under_resources' else 1)),SB_pairs=anchor['SB_pairs']+1,CB_sources=anchor['CB_sources']+4)
  result[mode]=budget_decide(mode,before,after,current_resources,new_resources,
   cpd_limit_s=anchor['CPD_s']*(1 if mode=='timing_under_resources' else 1.01),resource_limits=caps,
   native_valid=native_valid,transaction_complete=transaction_complete,resource_objectives=('wirelength',))
 return result
