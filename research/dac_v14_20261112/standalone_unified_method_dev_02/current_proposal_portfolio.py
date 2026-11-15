"""State-derived alternatives after a primary winning-path proposal is rejected.

The menu is fixed across circuits and policies. It is not a historical-quality
ranking. Every proposal still needs a real native transaction and exact current
acceptance; owner-only/target-only alternatives have no predicted CPD guarantee.
"""
import collections,hashlib,json
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha

def request_text(plan):
    """Render the existing free-path native interface for deduplication only."""
    removed=collections.defaultdict(set)
    for net,pin in plan['repair_pins']:removed[net].add(pin)
    text=str(len(removed))+'\n'
    for net,pins in sorted(removed.items()):text+=' '.join(map(str,[net,len(pins),*sorted(pins)]))+'\n'
    queries=plan['ordered_queries'];text+='0\n'+str(len(queries))+'\n'
    for row in queries:text+=f"{row['net']} {row['pin']} {row['raw_criticality']:.17g}\n"
    return text

def generate(base_plan,output):
    """Generate a primary-first menu solely from the current certified actions."""
    base_plan=Path(base_plan).resolve();output=Path(output).resolve();output.mkdir(exist_ok=False);plan=read(base_plan)
    assert plan['passed'] and all(sha(path)==h for path,h in plan['source_sha256'].items())
    state=Path(plan['source_state']).resolve();source=Path(read(state/'completion.json')['run']);assert read(state/'completion.json')['passed']
    targets={tuple(a['target']) for a in plan['actions']};donors={tuple(p) for a in plan['actions'] for p in a['donors']};wanted=targets|donors;sta={}
    if wanted:
        for line in (source/'native_sta_frontier.jsonl').open():
            row=json.loads(line)
            if row.get('type')=='pin' and (row['net'],row['pin']) in wanted:
                assert not row['driver'] and not row['ignored'] and not row['global'] and row['route_tree_present'];sta[row['net'],row['pin']]=row
                if len(sta)==len(wanted):break
        assert set(sta)==wanted
    files=[Path(__file__).resolve(),base_plan,state/'completion.json',state/'endpoint_vector.json',source/'routed.route',source/'native_sta_frontier.jsonl']
    bound={str(p):sha(p) for p in files};proposals=[];seen={};duplicates=[]
    def add(name,p,path):
        if not p['repair_pins']:return
        body=request_text(p);digest=hashlib.sha256(body.encode()).hexdigest()
        if digest in seen:duplicates.append(dict(name=name,same_native_request_as=seen[digest],request_sha256=digest));return
        seen[digest]=name
        if path is None:
            path=output/(name+'.plan.json');write(path,p)
        proposals.append(dict(name=name,plan=str(path),request_sha256=digest,repair_connections=len(p['repair_pins'])))
    add('primary',plan,base_plan)
    for name,pins,chosen in [('all_positive_combined',targets|donors,targets),('all_positive_target_only',targets,targets),('all_positive_owner_only',donors,set())]:
        if not pins:continue
        ordered=sorted(chosen,key=lambda key:(sta[key]['setup_slack_s'],key))+sorted(pins-chosen)
        candidate=dict(passed=True,source_state=str(state),actions=plan['actions'],selection=dict(status='state_derived_portfolio_alternative',targets=sorted(chosen),fraction=plan['selection'].get('fraction',.9),portfolio_variant=name),repair_pins=sorted(pins),ordered_queries=[dict(net=n,pin=p,raw_criticality=sta[n,p]['setup_criticality_raw']) for n,p in ordered],source_sha256=bound,native_calls=0,accepted=False,qualification='Alternative current-state proposal without a CPD/endpoint/resource improvement guarantee. Physical delays, native FULLSTA, fixed original budgets and exact per-policy acceptance remain mandatory.')
        add(name,candidate,None)
    result=dict(passed=True,source_state=str(state),base_plan=str(base_plan),fixed_order=['primary','all_positive_combined','all_positive_target_only','all_positive_owner_only'],proposals=proposals,duplicates=duplicates,source_sha256=bound,native_calls=0,qualification='One shared circuit-independent proposal order for all policies. The first admissible proposal advances that policy; rejected proposals do not exhaust the menu. Exact identical native requests within a state are deduplicated. No history-best selection or exhaustive resource-opportunity claim.')
    write(output/'portfolio.json',result);return result
