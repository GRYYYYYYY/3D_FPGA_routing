"""Exercise recovery02 on actual sealed LOADs with no native execution methods."""
from pathlib import Path
from types import SimpleNamespace
from retained_prefix_workflow import D, read, write, sha
from resource_checkpoint_recovery_v3 import Recovery

root = D/'native_checkpoint_adapter_v3_replay_01'
root.mkdir(exist_ok=False)
results, files = {}, [Path(__file__).resolve(), D/'resource_checkpoint_recovery_v3.py',D/'completed_native_worker_replay_v1.py',D/'pool_state_evaluator_v7.py',D/'sealed_native_pool_replay.py']
for name, old in [('bnn_R1_native', D/'stable_seed_transfer_dev_01/bnn_R1_native')]:
    reg = read(old/'registration.json')
    output = root/name
    output.mkdir()
    args = SimpleNamespace(domain_mode=reg['domain_mode'], domain_feedback=False,
        initial_state=Path(reg['initial_state']), bundle_size=reg['bundle_size'],
        seed_order=reg['seed_order'], graph_echo=reg['graph_echo'],
        accepted_steps=reg['local_probe']['accepted_steps'],
        rank_windows=reg['local_probe']['ranked_candidates_per_state'])
    failed = D/'native_checkpoint_recovery_01'/name
    poolreg = read(failed/'pool/registration.json')
    # Neither object has analyze/evaluate: unexpected execution cannot occur.
    pool = SimpleNamespace(command=poolreg['command'], inputs=poolreg['static_input_sha256'],
                           seed_order=poolreg['native_seed_order'], native_census=poolreg['native_resource_census'])
    evaluator = SimpleNamespace(directory=output/'evaluation_context_not_launched')
    adapter = Recovery(old, args, output)
    try:
        current = adapter.revalidate_checkpoint(evaluator, pool, echo=False)
        rn = len(adapter.steps)
        consumed=[]
        for rank in [0,1]:
            tx=output/f'round_{rn:03d}/candidate_{rank:02d}'
            tx.mkdir(parents=True)
            original_tx=old/f'round_{rn:03d}/candidate_{rank:02d}'
            result=adapter.consume(rn,rank,'reuse_off',current,original_tx/'request.txt',
                original_tx/'domain.txt',evaluator,tx,reg['anchor'])
            assert result and result['completed_search_consumed']
            assert result['new_native_search_calls']==result['new_native_LOAD_calls']==0
            assert result['reused_completed_revalidation']==(rank==0)
            assert result['materialized_completed_fused_candidate']==(rank==1)
            consumed.append(result)
            files.append(tx/'reuse_off_decisions.json')
        assert adapter.consume(999999,0,'reuse_off',current,Path('/not_used'),
            Path('/not_used'),evaluator,output,reg['anchor']) is None
        adapter.finish()
        results[name] = dict(passed=True, checkpoint_steps=rn, pending_candidates=consumed, previously_unexecuted_directory_returns_none=True,
                             no_native_or_evaluate_method_available=True,
                             original_root_anchor_unchanged=True, original_pool_final_seal_fabricated=False)
        files += [output/'recovery_registration.json', output/'checkpoint_revalidation.json',
                  output/'completed_search_reuse.json', tx/'reuse_off_decisions.json',
                  old/'registration.json', failed/'pool/registration.json']
    finally:
        for lock in adapter.locks:
            lock.close()
write(root/'completion.json', dict(passed=True, roles=results, native_calls_new=0,
      source_sha256={str(f): sha(f) for f in files},
      qualification='Actual v3 Recovery constructor/checkpoint/consume/finish methods replayed against real successfully sealed cached checkpoint and pending actual fused/LOAD states. Caller pool/evaluator stubs expose no native execution methods. Missing revalidation uses a separate read-only exact completed-worker replay facade whose analyze method always raises, real v7 materialization and a new complete independent physical audit. No native execution is possible. Lists/tuples normalized without sorting or numerical tolerance; exact vector, source, requests, native options, physical resources, decisions and original anchors rechecked. This does not exhaust remaining native menus, close R1/Tf roles, or supply a new workflow/runtime seal. Original jobs/directories unchanged.'))
print(dict(passed=True, roles={n:dict(checkpoint_steps=r['checkpoint_steps'],pending_accepted=[x['accepted'] for x in r['pending_candidates']]) for n,r in results.items()}, native_calls_new=0), flush=True)
