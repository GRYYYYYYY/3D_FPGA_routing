"""Commands for one freshly selected current-state proposal; shared by workflows."""
from retained_prefix_workflow import D

def commands(state,batch,query_graph,audit_cache,reuse_batches,fraction):
 cone=batch/'cone.json';cap=batch/'capacity';rel=batch/'relaxed';owner=batch/'owners';protected=batch/'protected';plan=batch/'proposal'
 args=['--reuse-root',batch.parents[1],'--state',state,'--batch',cap,'--query-graph',query_graph,'--audit-cache',audit_cache,'--cone',cone]
 for old in reuse_batches:args+=['--reuse-batch',old]
 return [
 ('current_sta_arrival_cone_compact.py',['--state',state,'--output',cone],'current_STA_selection'),
 ('run_current_cone_capacity_queries_cold_v1.py',args,'capacity_query'),
 ('audit_current_cone_queries.py',['--batch',cap,'--query-graph',query_graph,'--audit-cache',audit_cache],'capacity_audit'),
 ('run_current_graph_relaxed_queries_cold_v1.py',['--reuse-root',batch.parents[1],'--capacity-batch',cap,'--batch',rel,'--query-graph',query_graph]+[item for old in reuse_batches if (old.parent/'relaxed/analysis.json').exists() for item in ['--reuse-batch',old.parent/'relaxed']],'relaxed_query'),
 ('audit_current_cone_queries.py',['--batch',rel,'--query-graph',query_graph,'--audit-cache',audit_cache],'relaxed_audit'),
 ('derive_current_release_opportunities.py',['--capacity-batch',cap,'--relaxed-batch',rel,'--state',state,'--output',owner,'--audit-cache',audit_cache],'current_owner_feedback'),
 ('query_current_protected_critical.py',['--capacity-batch',cap,'--opportunities',owner/'completion.json','--output',protected,'--audit-cache',audit_cache,'--query-graph',query_graph],'protected_query'),
 ('plan_current_critical_group.py',['--cone',cone,'--capacity-batch',cap,'--protected',protected/'completion.json','--audit-cache',audit_cache,'--output',plan,'--fraction',fraction],'current_group_plan')]
