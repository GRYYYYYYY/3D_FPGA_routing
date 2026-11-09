#!/usr/bin/env python3
"""Verify input isolation, build identity and independent route audits for v2."""
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import fcntl
from pathlib import Path

from lazagna_common import ROOT,sha256,utc,write_json
from three_baseline_common import read
from validate_lazagna_vtr9_pilot import placements
from validate_three_baselines import normalized
from run_h3d_delay_study import option,route_body_hash

BASE=ROOT/'results/h3d_delay_20261027_v2'


def audit_group(group):
    import validate_three_baselines as validator
    validator.BASE=BASE
    return validator.audit_group('native',group,{})


def main():
    lock=(BASE/'validator.lock').open('w')
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not (BASE/'validation.json').exists()
    protocol=read(BASE/'protocol.json')
    for phase in ['pilot','main','serial']:
        state=read(BASE/(phase+'_state.json'))
        assert state['stage']=='finished'
        assert set(state['finished'])=={j['name'] for j in protocol['jobs'] if j['phase']==phase}
    cache={}
    def digest(p):
        p=str(Path(p).resolve())
        if p not in cache: cache[p]=sha256(p)
        return cache[p]
    frozen=read(BASE/'source_lock.json')['protected']
    for p,h in frozen.items(): assert digest(ROOT/p)==h,p
    for p,h in protocol['bindings'].items(): assert digest(p)==h,p
    artifact=Path(protocol['binary']).parent
    build=read(artifact/'manifest.json')
    assert digest(artifact/'vpr')==build['binary_sha256']==protocol['binary_sha256']
    for p,h in build['new_source_sha256'].items():
        assert digest(artifact/'new_sources'/p)==h
        assert digest(ROOT/'vendor/vtr'/p)==h
    assert digest(artifact/'changes.patch')==build['patch_sha256']
    results=[read(BASE/'runs'/j['name']/'result.json') for j in protocol['jobs']]
    groups=defaultdict(list); pairs=defaultdict(list); headers=[]
    for result in results:
        directory=Path(result['directory']); receipt=read(directory/'manifest.json')
        assert receipt['status'] in ('completed','failed','timeout')
        assert receipt['environment']==protocol['environments'][result['arm']]
        if result['arm'] in ('delay','delay_critical','budget1'):
            assert result['stats']['H3D_DELAY_INIT']['zero_rc']=='1'
            assert result['stats']['H3D_DELAY_INIT']['budget']==receipt['environment']['VPR_H3D_DELAY_BUDGET']
        source=read(result['source_manifest'])
        for p,h in receipt['inputs'].items():
            if digest(p)!=h:
                assert p==str(directory/'fixed.place')
                assert placements(p)==placements(option(source['command'],'--place_file'))
                headers.append(result['name'])
        for p,h in result['source_hashes'].items(): assert digest(p)==h
        for record in result['outputs'].values(): assert digest(record['path'])==record['sha256']
        assert digest(directory/'packed.net')==digest(option(source['command'],'--net_file'))
        assert placements(directory/'fixed.place')==placements(option(source['command'],'--place_file'))
        pairs[result['fixture']].append(normalized(receipt['command']))
        if result['native_legal']:
            assert receipt['status']=='completed'
            assert result['metrics']['native_full_check_passed'] and result['metrics']['routing_success_reported']
            assert route_body_hash(directory/'routed.route')==result['route_body_sha256']
            with (directory/'routed.route').open() as f:
                assert digest(directory/'fixed.place') in f.readline()
            groups[result['graph']].append(result)
    for fixture,commands in pairs.items(): assert all(c==commands[0] for c in commands),fixture
    # Retain and audit the four legal outputs of the rejected pilot revision
    # as well; the two assertion failures stay in their own attempt denominator.
    prior=ROOT/'results/h3d_delay_20261027'
    prior_results=[read(p) for p in sorted((prior/'runs').glob('*/result.json'))]
    assert len(prior_results)==6 and sum(r['native_legal'] for r in prior_results)==4
    for result in prior_results:
        directory=Path(result['directory']);receipt=read(directory/'manifest.json')
        assert receipt['status'] in ('completed','failed')
        source=read(result['source_manifest'])
        for p,h in receipt['inputs'].items():
            if digest(p)!=h:
                assert p==str(directory/'fixed.place')
                assert placements(p)==placements(option(source['command'],'--place_file'))
        for record in result['outputs'].values():assert digest(record['path'])==record['sha256']
        if result['native_legal']:
            assert result['metrics']['native_full_check_passed'] and result['metrics']['routing_success_reported']
            assert route_body_hash(directory/'routed.route')==result['route_body_sha256']
            groups[result['graph']].append({**result,'name':'prior_'+result['name']})
    audits=[]
    with ProcessPoolExecutor(max_workers=3) as pool:
        for group in pool.map(audit_group,groups.values()): audits.extend(group)
    assert all(a['passed'] for a in audits)
    write_json(BASE/'validation.json',dict(utc=utc(),passed=True,registered=len(protocol['jobs']),
        attempted=len(results),full_and_audited=sum(not a['name'].startswith('prior_') for a in audits),
        prior_pilot_attempts=6,prior_pilot_failures=2,prior_pilot_full_and_audited=4,
        audits=audits,graph_groups=len(groups),
        frozen_files_unchanged=len(frozen),unique_files_rehashed=len(cache),
        private_header_changes=headers,paired_fixture_count=len(pairs),
        protocol_sha256=digest(BASE/'protocol.json'),source_lock_sha256=digest(BASE/'source_lock.json')))


if __name__=='__main__': main()
