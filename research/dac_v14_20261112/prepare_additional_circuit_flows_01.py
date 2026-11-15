"""Freeze two extra known-circuit pairs before observing new policy results."""
import copy
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

root = D / 'complete_serial_additional_circuits_01'
assert not root.exists()
template_path = D / 'complete_serial_lazy_transfer_dev_01/configs/softmax_paired.json'
template = read(template_path)
oldcmd = template['route_command']
def inputs(command):
    return [command[1], command[2], *[command[command.index(k)+1] for k in ['--read_rr_graph', '--net_file', '--place_file']]]
base_hashes = {p: h for p, h in template['input_sha256'].items() if p not in inputs(oldcmd)}
root.mkdir()
(root / 'configs').mkdir()
cases, provenance = {}, {}
hashes = {}
def digest(p):
    p = str(Path(p).resolve())
    if p not in hashes:
        hashes[p] = sha(p)
    return hashes[p]
for circuit in ['conv_layer', 'robot_rl']:
    source = D.parents[1] / 'results/architecture_flow_20261027/runs' / f'heldout_{circuit}_s21_hybrid_o_n60_w100_p0_a0'
    manifest = read(source / 'manifest.json')
    prior = manifest['command']
    assert Path(prior[2]).stem == circuit
    assert prior[prior.index('--route_chan_width')+1] == '100'
    for option, name in [('--net_file', 'packed.net'), ('--place_file', 'placed.place')]:
        assert Path(prior[prior.index(option)+1]) == source / name
        assert digest(source/name) == manifest['outputs'][name]['sha256']
    command = list(oldcmd)
    command[1:3] = prior[1:3]
    for option in ['--read_rr_graph', '--net_file', '--place_file', '--device', '--route_chan_width']:
        command[command.index(option)+1] = prior[prior.index(option)+1]
    assert command[command.index('--seed')+1] == '11'
    assert command[command.index('--router_max_convergence_count')+1] == '2'
    assert command[command.index('--route_file')+1] == '<fresh output assigned inside measured command>'
    for mode, paired in [('native', False), ('domain', True)]:
        config = copy.deepcopy(template)
        config.update(circuit=circuit, route_command=command, domain_mode='paired' if paired else 'unrestricted',
                      domain_feedback=paired, initial_route_imported=False, full_graph_cache=None,
                      backend='domain_first_stop_on_resource_accept', native_reuse_allowed=False,
                      input_sha256=dict(base_hashes), source_manifest=str(source/'manifest.json'),
                      source_manifest_sha256=digest(source/'manifest.json'),
                      comparison='Prospectively frozen K8/rank3/delay-RR-ID0.2ns resource policy on an additional known circuit; own-current native/domain branches have identical fresh-route inputs/options and immutable root CPD/wire+0.1% envelopes. Not an unseen-circuit or statistical speedup claim.',
                      qualification='Known-circuit policy transfer. Historical folder names containing heldout refer to an older study and are not adopted as a new held-out designation. Only explicit architecture/RRG/BLIF/packed/place bytes are inputs; no old route, query, repair or quality/time result imported. All new graph-index construction, route and complete real repair/checks/rollback inside the measured command. Preserve every failed role, rejected candidate, zero-cut and no-gain outcome.')
        config['input_sha256'].update({p: digest(p) for p in inputs(command)})
        for f in [Path(__file__).resolve(), D/'verify_complete_serial_additional_policy_v1.py']:
            config['input_sha256'][str(f)] = digest(f)
        name = circuit + '_' + mode
        path = root / 'configs' / (name+'.json')
        write(path, config)
        cases[name] = str(path)
    provenance[circuit] = dict(source_manifest=str(source/'manifest.json'),
                              source_manifest_sha256=digest(source/'manifest.json'),
                              input_files={p: digest(p) for p in inputs(command)},
                              policy_result_observed_before_registration=False)
write(root/'plan.json', dict(fixed_order=list(cases), cases=cases,
      predecessor=str(D/'R1_owner_release_joint_probe_01/queue'), input_provenance=provenance,
      source_sha256={str(Path(__file__).resolve()): sha(__file__), str(template_path): sha(template_path)},
      selection='Circuit names conv_layer and robot_rl chosen from existing n60/w100 Hybrid-O pack/place inputs, without consulting new fixed-policy routing/repair results. Two new circuit identities relative to the22complete configurations; known historical circuits, not new held-out test labels.',
      qualification='Four actual complete new-route own-current native/domain roles with frozen current policy and explicit existing packed/placed inputs. Same router seed11/count2, K8/rank3,0.2ns screen and delay/RR-ID everywhere; paired mode uses domain-first acceptance with failure release and verified skipped OFF controls. Different trajectories retain own successors. All failed/zero-effect outcomes and actual costs retained; no best-of selection, borrowed route/quality/time, new convergence opportunity or statistical speedup. Native work remains behind the same blocking global serial slot.'))
print(dict(prepared=True, circuits=list(provenance), registered_roles=4), flush=True)
