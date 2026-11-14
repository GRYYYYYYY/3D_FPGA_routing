#!/usr/bin/env python3
"""Replay sealed real transactions through a new audit, without invoking VPR."""
import copy
import os
from pathlib import Path
import resource
import time

from direct_native_transaction_audit import DirectTransactionAudit, check_scope, parse_transaction
from retained_prefix_workflow import D, read, sha, write
from export_policy_analysis_pool import process_identity
from coordinated_repair_tree import from_trace
from resource_opportunity_census import stream_trace

b = D/'direct_native_transaction_validation_01'
b.mkdir(exist_ok=False)
resource.setrlimit(resource.RLIMIT_AS, (64*1024**3,64*1024**3))
started = time.monotonic()
actors = [D/'fused_resource_development_01'/name for name in [
    'eltwise_A0_native_only_K8','eltwise_A0_feedback_K8','bnn_A0_native_only_K8']]
files = [Path(__file__).resolve(), D/'direct_native_transaction_audit.py']
cases = []
for actor in actors:
    assert read(actor/'completion.json')['passed'] and read(actor/'evaluation_context/input_seal.json')['passed']
    files.extend([actor/'completion.json',actor/'evaluation_context/input_seal.json'])
    workers = sorted(actor.glob('round_*/candidate_*/reuse_*_worker_receipt.json'))
    # First accepted and last (legal rejected or accepted) transactions in each
    # sealed actor; this rule is fixed and never chooses by quality improvement.
    chosen = list(dict.fromkeys([workers[0],workers[-1]]))
    for path in chosen:
        role_name = path.name.removesuffix('_worker_receipt.json')
        tx = path.parent
        role = read(tx/'registration.json')['roles'][role_name]
        reference = tx/(role_name+'_audit/analysis.json')
        assert read(reference)['passed']
        cases.append((actor.name,path,role_name,role,reference))
        files.extend([path,tx/'registration.json',reference])
bindings = {str(p):sha(p) for p in files}
write(b/'registration.json',dict(pid=os.getpid(),start_ticks=process_identity(os.getpid())['start_ticks'],
    source_sha256=bindings, cases=[str(c[1]) for c in cases],native_calls=0,route_calls=0,
    question='Can actual native candidate scope be checked directly, preserving the old retained/terminal/edge/capacity proof without reconstructing another serialized route?',
    qualification='Read-only engineering replay of sealed actual transactions, including accepted and legal-rejected states. Not new route experiments, runtime confirmation or a faster algorithm result.'))
contexts = {}
results = []
negative = []
for index,(actor,path,name,role,reference_path) in enumerate(cases):
    worker = read(path)
    registry = read(Path(worker['job']).parent/'registration.json')
    command = registry['command']
    graph = Path(command[command.index('--read_rr_graph')+1])
    parent = path.parents[2]
    cache = Path(read(parent/'registration.json')['audit_cache'])
    key = (str(graph),str(cache))
    if key not in contexts:
        contexts[key] = DirectTransactionAudit(graph,cache)
    context = contexts[key]
    write(b/'status.json',dict(status='auditing_actual_candidate',case=index,worker=str(path)))
    actual = context.audit(worker,role,b/f'case_{index:02d}')
    reference = read(reference_path)
    for k in ['queries','attempts','native_transaction_seconds']:
        assert actual[k] == reference[k], (index,k)
    assert bool(actual['candidate_route']) == bool(reference['candidate_route'])
    assert {r['net']:r for r in actual.get('scope',[])} == {r['net']:r for r in reference.get('scope',[])}
    norm = lambda rows: sorted(rows,key=lambda r:(r['net'],r['pin']))
    assert norm(actual.get('changed_delays',[])) == norm(reference.get('changed_delays',[]))
    # Old audit's reconstructed route is already compared against this actual
    # candidate in the sealed actor. Do not repeat that expensive full parse.
    results.append(dict(case=index,actor=actor,worker=str(path),passed=True,
        direct_seconds=actual['complete_direct_audit_seconds'],
        old_recorded_audit_seconds=reference['audit_and_serialization_seconds'],
        old_time_is_a_separate_historical_component=True,
        actual_candidate_route=actual['candidate_route'],reference=str(reference_path)))
    write(b/'results.json',results)
    print(dict(case=index,actor=actor,direct_seconds=actual['complete_direct_audit_seconds']),flush=True)
    if index == 0:
        parsed = parse_transaction((Path(worker['native_directory'])/'joint_native.log').read_text(),role['queries'])
        net = min(parsed['raw'])
        source = next(r for r in stream_trace(Path(role['source'])/'routed.route') if r['net']==net)
        target = next(r for r in stream_trace(actual['candidate_route']) if r['net']==net)
        original = from_trace(source['trace'],context.cache.switches)
        candidate = from_trace(target['trace'],context.cache.switches)
        def reject(label, tree, raw, kept, removed):
            try: check_scope(original,tree,raw,kept,removed,context.cache.switches)
            except (AssertionError,KeyError): negative.append(label)
            else: raise AssertionError('Scope corruption admitted: '+label)
        raw=parsed['raw'][net];kept=parsed['kept'][net];removed=role['removed_pins'][str(net)]
        changed=copy.deepcopy(candidate);pin=min(changed['sinks']);changed['sinks'][pin]=changed['root']
        reject('changed_terminal_mapping',changed,raw,kept,removed)
        reject('wrong_retained_set',candidate,raw,kept|{-999},removed)
        reject('missing_logged_node',candidate,raw[:-1],kept,removed)
        reject('missing_requested_pin',candidate,raw,kept,removed+[max(original['sinks'])+1])
        malformed=(Path(worker['native_directory'])/'joint_native.log').read_text().replace('occupancy_restored','occupancy_not_restored')
        try:parse_transaction(malformed,role['queries'])
        except AssertionError:negative.append('unrestored_native_transaction')
        else:raise AssertionError('Unrestored transaction admitted')
        forged=copy.deepcopy(worker);forged['route_sha256']='0'*64
        try:context.audit(forged,role,b/'forged_source_receipt')
        except AssertionError:negative.append('forged_source_receipt')
        else:raise AssertionError('Forged native source admitted')
assert all(sha(p)==h for p,h in bindings.items())
for context in contexts.values():context.require_static()
write(b/'completion.json',dict(passed=True,cases=len(results),results=results,negative_controls=negative,
    native_calls=0,route_calls=0,complete_component_validation_seconds=time.monotonic()-started,
    complete_single_configuration_algorithm_seconds=None,
    source_sha256={str(p):sha(p) for p in [b/'registration.json',b/'results.json',*map(Path,bindings)]},
    qualification='Direct scope checks match old reconstruction checks on six predetermined sealed actual transactions. Current replay runtime is not paired with historical component runtime as a formal speedup. Full native/independent physical/STA and domain gates still required; this does not yet integrate a fast acceptance actor.'))
write(b/'status.json',dict(status='passed'))
print(dict(passed=True,cases=len(results),negative_controls=negative),flush=True)
