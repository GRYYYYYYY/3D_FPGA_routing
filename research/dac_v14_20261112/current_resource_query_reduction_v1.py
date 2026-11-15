"""Keep batching unless a complete-cut budget reduces proposed queries substantially."""
from current_resource_bundle_v2 import select_cuts as net_group
from current_resource_connection_budget_v1 import select_cuts as budget_group

def select_cuts(candidates,size,start=0,*,connection_budget,reduction_factor=2):
    assert type(reduction_factor) is int and reduction_factor>=2
    full=net_group(candidates,size,start)
    limited=budget_group(candidates,size,start,connection_budget=connection_budget)
    if not full:return []
    assert limited
    full_queries=sum(len(c['ordered_queries']) for c in full)
    limited_queries=sum(len(c['ordered_queries']) for c in limited)
    # This is a registered development heuristic, not a wall-time model:
    # preserve full network cuts and avoid fragmenting batches for small savings.
    return limited if reduction_factor*limited_queries<=full_queries else full
