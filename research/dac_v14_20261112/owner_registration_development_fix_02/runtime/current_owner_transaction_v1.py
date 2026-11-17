"""Prepare a current owner-coordination transaction without a historical template."""
import argparse
import math
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from run_native_scope_policy_v4 import run_dir
from current_resource_bundle_v2 import serialize_request
from endpoint_timing_policy_streaming_v2 import compare
from controller_runtime import package_files
from owner_runtime_registration_v2 import bind_runtime


def physical_identity(state):
    run = run_dir(state)
    manifest = read(run/'manifest.json')
    assert manifest['metrics']['native_full_check_passed']
    cmd = manifest['command']
    inputs = [cmd[1], cmd[2], cmd[cmd.index('--read_rr_graph')+1]]
    # Bind physical inputs, not executable/configuration provenance aliases.
    identity = []
    for name in inputs:
        record = manifest['shared_inputs'][str(name)]
        identity.append(record['sha256'])
    identity += [sha(run/'packed.net'), sha(run/'placed.place')]
    return identity


def root_envelope(root):
    root = Path(root).resolve()
    assert read(root/'completion.json')['passed']
    audit = read(run_dir(root)/'independent_audit.json')
    assert audit['audit']['passed']
    metrics = audit['physical_metrics']
    vector = read(root/'endpoint_vector.json')
    assert math.isfinite(vector['cpd_s']) and vector['cpd_s'] >= 0
    axes = dict(wirelength=metrics['planar_wirelength_excluding_sb_half_nodes'],
                SB_pairs=metrics['sb_pairs_used'], CB_sources=metrics['cb_crossing_output_sources_used'])
    return dict(CPD_s=vector['cpd_s'], **axes), dict(axes, wirelength=(axes['wirelength']*1001+999)//1000)


def prepare(state, root_state, selection, full_graph_cache, output, rank=0,
            domain_mode='unrestricted', seed_order='delay_rr_id', *, runtime_config):
    """The caller owns the serial slot and runs the returned registered backend."""
    state, root_state, selection, cache, output = [Path(p).resolve() for p in
        [state, root_state, selection, full_graph_cache, output]]
    assert not output.exists(), 'Never overwrite an existing transaction'
    assert type(rank) is int and rank >= 0
    assert domain_mode in ['unrestricted', 'matched_target_CB']
    assert seed_order in ['native', 'rr_id', 'delay_rr_id']
    selected = read(selection/'completion.json')
    assert selected['passed'] and Path(selected['state']).resolve() == state, 'Stale/foreign selection'
    assert all(sha(f)==h for f,h in selected['source_sha256'].items()), 'Selection source changed'
    assert all(sha(selection/f)==h for f,h in selected['artifact_sha256'].items()), 'Selection artifacts changed'
    assert read(state/'completion.json')['passed']
    assert physical_identity(state) == physical_identity(root_state), 'Different physical input/root'
    before, root_vector = [read(s/'endpoint_vector.json') for s in [state,root_state]]
    assert compare(root_vector,before)['compatible'], 'Different constraints or endpoint mapping'
    anchor, limits = root_envelope(root_state)
    cached = read(cache/'completion.json')
    assert cached['passed'] and cached['graph_sha256'] == physical_identity(state)[2]
    audit_cache = Path(cached['parent_cache'])
    assert read(audit_cache/'completion.json')['passed']
    groups = read(selection/'groups.json')
    assert len(groups) == selected['eligible_joint_groups']
    files = [*package_files(), selection/'completion.json',selection/'groups.json',selection/'certificates.json',cache/'completion.json',audit_cache/'completion.json']
    for s in [state,root_state]:
        files += [s/'completion.json', s/'endpoint_vector.json', run_dir(s)/'manifest.json',
                  run_dir(s)/'routed.route', run_dir(s)/'packed.net', run_dir(s)/'placed.place',
                  run_dir(s)/'independent_audit.json']
    bound = {str(f):sha(f) for f in files}
    if rank >= len(groups):
        output.mkdir(parents=True)
        result = dict(passed=True,status='no_eligible_owner_group_at_rank',rank=rank,
                      eligible_groups=len(groups),state=str(state),root_state=str(root_state),
                      native_calls_new=0,source_sha256=bound,transaction_registered=False)
        write(output/'preparation.json',result)
        return result
    group=groups[rank]
    assert group['eligible'] and group['target_screen']['eligible'] and group['owner_screen']['eligible']
    certificates={r['net']:r for r in read(selection/'certificates.json')}
    cert=certificates[group['target_net']]
    assert cert['status']=='frozen_other_routes_force_two_distinct_crossing_resources'
    assert any(x['owner_net']==group['owner_net'] and x['node']==group['escape_node'] and
               x['capacity']==1 for x in cert['local_exits'])
    assert group['target_pins']==cert['target_pins'] and group['target_net']!=group['owner_net']
    cuts=[]
    for net,pins in [(group['target_net'],group['target_pins']),(group['owner_net'],group['owner_pins'])]:
        assert pins and len(pins)==len(set(pins))
        cuts.append(dict(net=net,pins=pins,ordered_queries=[q for q in group['queries'] if q['net']==net]))
    request,_,queries=serialize_request(cuts)
    assert request==group['request'] and queries==group['queries']
    assert {(q['net'],q['pin']) for q in queries}=={(c['net'],p) for c in cuts for p in c['pins']}
    assert len(queries)==group['connections']
    output.mkdir(parents=True)
    req=output/'request.txt';req.write_text(request)
    domain=output/'domain_nets.txt';domain.write_text(f"1\n{group['target_net']}\n")
    explicit=output/'target_CB_sources.txt';explicit.write_text(f"1\n{group['target_net']} 1 {cert['only_OPIN']}\n")
    bound.update({str(f):sha(f) for f in [req,domain,explicit]})
    roles={}
    for enabled in ([False,True] if domain_mode=='matched_target_CB' else [False]):
        name='joint_target_CB_domain' if enabled else 'joint_native'
        roles[name]=dict(state=str(state),source=str(run_dir(state)),baseline='own_current_state',
            scope='current_capacity_certified_target_plus_blocking_owner',request=str(req),queries=queries,
            removed_pins={str(c['net']):c['pins'] for c in cuts},objective='weighted_soft',
            fixed_target_paths=False,crossing_reuse_enabled=enabled,domain_failure_release=False,
            seed_order=seed_order,original_budget=anchor,fixed_resource_limits=limits,
            crossing_domain=str(domain),explicit_crossings=str(explicit) if enabled else None,
            allowed_resource_kind='CB' if enabled else None,source_sha256=bound)
    registration=dict(roles=roles,full_graph_cache=str(cache),audit_cache=str(audit_cache),
        limits=dict(child_seconds=1800,memory_bytes=64*1024**3,disk_reserve_bytes=80*1024**3),
        current_resource_selector_after_commit=True,source_sha256=bound,
        root_state=str(root_state),owner_selection=str(selection),owner_rank=rank,
        resource_conditions=dict(anchor=anchor,resource_limits=limits,resource_objectives=['SB_pairs','CB_sources']))
    registration=bind_runtime(registration,runtime_config)
    write(output/'registration.json',registration)
    result=dict(passed=True,status='registered_current_owner_scope',transaction_registered=True,
        state=str(state),root_state=str(root_state),rank=rank,selected_group=group,
        anchor=anchor,resource_limits=limits,roles=list(roles),native_calls_new=0,
        backend=str(D/'run_joint_crossing_source_transactions_v2.py'),
        source_sha256=bound,registration_sha256=sha(output/'registration.json'),
        qualification='Constructed from current certified capacity/STA selection and the supplied immutable root. No historical transaction/template or benchmark-specific identifiers imported. Default owner search is unrestricted in both unified arms; matched target-CB domains are a separate attribution mode. Preparation alone establishes neither native feasibility nor performance.')
    write(output/'preparation.json',result)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for flag in ['state','root-state','selection','full-graph-cache','output']:
        p.add_argument('--'+flag,type=Path,required=True)
    p.add_argument('--rank',type=int,default=0)
    p.add_argument('--domain-mode',choices=['unrestricted','matched_target_CB'],default='unrestricted')
    p.add_argument('--seed-order',choices=['native','rr_id','delay_rr_id'],default='delay_rr_id')
    p.add_argument('--runtime-config',type=Path,required=True)
    a=p.parse_args();r=prepare(a.state,a.root_state,a.selection,a.full_graph_cache,a.output,a.rank,a.domain_mode,a.seed_order,runtime_config=a.runtime_config)
    print({k:r[k] for k in ['passed','status','transaction_registered','native_calls_new']},flush=True)
