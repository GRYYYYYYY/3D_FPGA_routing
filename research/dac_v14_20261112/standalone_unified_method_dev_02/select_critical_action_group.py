"""Bounded branch-and-bound over exact current-path action patterns.

The budget protects one planning call. It never ends the research goal. A timed
out planner returns its feasible incumbent with optimality explicitly unknown.
"""
import math,time
from critical_action_patterns import evaluate

def select(pattern_data,actions,fraction=.9,timeout_seconds=300.):
 assert math.isfinite(fraction) and 0<fraction<=1 and timeout_seconds>0
 start=time.monotonic();all_ids=tuple(range(len(actions)));full=evaluate(pattern_data,actions,all_ids);maximum=full['min_current_winning_path_gain_ns'];threshold=fraction*maximum
 if maximum<=0:return dict(status='no_positive_current_path_cover',selected=[],profile=full,exact_within_proxy=True,visited_nodes=0)
 best_ids=all_ids;best=full;visited=0;complete=True
 def rank(ids,p):return (p['repair_connections'],-p['min_current_winning_path_gain_ns'],sorted(tuple(actions[i]['target']) for i in ids))
 def dfs(i,chosen):
  nonlocal best_ids,best,visited,complete
  if time.monotonic()-start>=timeout_seconds:complete=False;return
  visited+=1;p=evaluate(pattern_data,actions,chosen)
  if p['repair_connections']>best['repair_connections']:return
  if p['min_current_winning_path_gain_ns']>=threshold and rank(chosen,p)<rank(best_ids,best):best_ids=chosen;best=p
  if i==len(actions):return
  upper=evaluate(pattern_data,actions,chosen+tuple(range(i,len(actions))))
  if upper['min_current_winning_path_gain_ns']<threshold:return
  dfs(i+1,chosen+(i,))
  if complete:dfs(i+1,chosen)
 dfs(0,())
 assert best['all_current_paths_covered'] and best['min_current_winning_path_gain_ns']>=threshold
 return dict(status='exact_proxy_selection' if complete else 'feasible_incumbent_time_guard',selected=list(best_ids),targets=sorted(tuple(actions[i]['target']) for i in best_ids),profile=best,
  maximum_proxy_gain_ns=maximum,fraction=fraction,threshold_proxy_gain_ns=threshold,exact_within_proxy=complete,visited_nodes=visited,complete_planning_seconds=time.monotonic()-start,
  qualification='Selected scope is timing-only/proxy-feasible; native capacity replacement, complete legality/STA and fixed design budgets still decide commit. Patterns can scale exponentially in action count even when physical path enumeration is compressed.')
