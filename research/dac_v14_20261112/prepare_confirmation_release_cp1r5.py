"""Freeze the exact owner preparation/runtime identity correction, checker only."""
import ast
import copy
import fcntl
import json
import os
import shutil
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
from owner_registration_transition_v1 import verify_transition

HOME_ROOT = Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home')
OLD = HOME_ROOT/'confirmation_releases/current_sta_cp1r4'
ROOT = HOME_ROOT/'confirmation_releases/current_sta_cp1r5'
OUT = D/'confirmation_release_cp1r5_01'
CHECKER = 'verify_complete_unified_method_v1.py'
HELPER = 'owner_registration_transition_v1.py'
BEFORE = "  assert prep['passed'] and prep['transaction_registered'] and prep['registration_sha256']==sha(tx/'registration.json')"
AFTER = "  assert verify_transition((tx/'registration.json').read_bytes(),prep,read(tx/'execution_registration.json'),rreg,resource_flow/'phase_runtime.json',(resource_flow/'phase_runtime.json').read_bytes())"
IMPORT = 'from owner_registration_transition_v1 import verify_transition\n'
EVIDENCE = "  files += [tx/'execution_registration.json',resource_flow/'phase_runtime.json']\n"


def main():
    started = time.monotonic()
    plan = read(OUT/'plan.json')
    with (D/'critical_scope_runner.lock').open() as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert all(sha(p) == h for p,h in plan['source_sha256'].items())
        parent = read(OLD/'release_manifest.json')
        assert sha(OLD/'release_manifest.json') == plan['parent_manifest_sha256']
        assert all(sha(OLD/p) == h for p,h in parent['files_sha256'].items())
        assert not ROOT.exists() and not (OUT/'completion.json').exists()
        source = (OLD/'runtime'/CHECKER).read_text()
        assert source.count(BEFORE) == 1 and IMPORT not in source
        revised = IMPORT + source.replace(BEFORE, AFTER+'\n'+EVIDENCE.rstrip('\n'))
        assert revised.replace(IMPORT,'',1).replace(AFTER+'\n'+EVIDENCE.rstrip('\n'),BEFORE,1) == source
        compile(revised, CHECKER, 'exec')
        old_asserts = [ast.dump(n) for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Assert)]
        new_asserts = [ast.dump(n) for n in ast.walk(ast.parse(revised)) if isinstance(n,ast.Assert)]
        assert len(old_asserts)==len(new_asserts)==88
        assert sum(x!=y for x,y in zip(old_asserts,new_asserts))==1

        # Invoke the exact new expression on three original owner transactions.
        # No whole-arm replay, new native query, or historical receipt mutation.
        cohort = read(D/'cp1r3_distinct_input_cohort_01/plan.json')
        case = Path(cohort['inputs'][0]['workspace'])/'native'
        resource_flow = case/'flow/resource_flow'
        rreg = read(resource_flow/'repair/registration.json')
        expression = compile(AFTER.strip()[7:], '<new-owner-assert>', 'eval')
        receipts = []
        negative_guards = 0
        for rank in range(3):
            tx = resource_flow/f'repair/round_004/owner_{rank:02d}'
            prep = read(tx/'preparation.json')
            result = eval(expression, dict(verify_transition=verify_transition,read=read),
                          dict(tx=tx,prep=prep,rreg=rreg,resource_flow=resource_flow))
            assert result['mode']=='exact_documented_pre_execution_runtime_binding'
            runtime = resource_flow/'phase_runtime.json'
            raw = (tx/'registration.json').read_bytes()
            execution = read(tx/'execution_registration.json')
            actual = json.loads(raw)
            changed = copy.deepcopy(actual)
            changed['roles']['joint_native']['queries'][0]['pin'] += 1
            data = (json.dumps(changed,indent=2)+'\n').encode()
            import hashlib
            resealed = {**execution,'registration_sha256':hashlib.sha256(data).hexdigest()}
            for args in [(data,prep,resealed,rreg,runtime,runtime.read_bytes()),
                         (raw,prep,execution,rreg,runtime,runtime.read_bytes()+b'\n'),
                         (raw,prep,{**execution,'registration_sha256':'0'*64},rreg,runtime,runtime.read_bytes())]:
                try:
                    verify_transition(*args)
                except (AssertionError,KeyError):
                    negative_guards += 1
                else:
                    raise AssertionError('Unauthorized transition accepted')
            receipts.append(dict(transaction=str(tx),result=result,source_sha256={
                str(p):sha(p) for p in [tx/'registration.json',tx/'preparation.json',
                tx/'execution_registration.json',runtime,resource_flow/'repair/registration.json']}))
        validation = dict(passed=True,exact_reversible_source_edit=True,original_assert_nodes=88,
                          changed_assert_nodes=1,actual_owner_rows=receipts,negative_guards=negative_guards,
                          new_native_or_STA_calls=0,whole_arm_replay=False,
                          historical_failures_unchanged=True,ctime_exception_installed=False)
        write(OUT/'checker_validation.json',validation)
        shutil.copytree(OLD,ROOT,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        ROOT.chmod(0o755); (ROOT/'runtime').chmod(0o755)

        def replace(path,text):
            if path.exists():path.chmod(0o644)
            path.write_text(text)

        replace(ROOT/'runtime'/CHECKER,revised)
        shutil.copyfile(D/HELPER,ROOT/'runtime'/HELPER)
        artifact = read(OLD/'runtime/artifact_manifest.json')
        for name in [CHECKER,HELPER]:artifact['sha256'][name]=sha(ROOT/'runtime'/name)
        artifact['component_revision']='complete_method_cp1r5_owner_identity_checker'
        artifact['qualification']='CP1r4 algorithm bytes unchanged. Checker admits only exact preparation-to-runtime binding already sealed by execution and parent; all other original checks retained. No ctime exception or historical receipt rewrite.'
        replace(ROOT/'runtime/artifact_manifest.json',json.dumps(artifact,indent=2)+'\n')
        assert all(sha(ROOT/'runtime'/p)==h for p,h in artifact['sha256'].items())
        changed=[p for p,h in parent['files_sha256'].items() if p.startswith('runtime/') and sha(ROOT/p)!=h]
        assert set(changed)=={'runtime/artifact_manifest.json','runtime/'+CHECKER}
        added=[str(p.relative_to(ROOT)) for p in (ROOT/'runtime').rglob('*') if p.is_file() and str(p.relative_to(ROOT)) not in parent['files_sha256']]
        assert added==['runtime/'+HELPER]
        entry=(OLD/'confirmation.py').read_text()
        assert entry.count("m['release_id']=='current_sta_cp1r4'")==1
        replace(ROOT/'confirmation.py',entry.replace("m['release_id']=='current_sta_cp1r4'","m['release_id']=='current_sta_cp1r5'"))
        contract=read(OLD/'contract.json'); original=copy.deepcopy(contract)
        contract.update(release_id='current_sta_cp1r5',
            internal_compatibility_tag='CP1r4 algorithm plus exact owner preparation/runtime seal reconciliation in independent checker only.',
            current_execution_boundary='Checker expression validated against three actual owner records and adversarial mutations; no CP1r5 full confirmation yet.')
        for key in original:
            if key not in ['release_id','internal_compatibility_tag','current_execution_boundary']:
                assert contract[key]==original[key],key
        replace(ROOT/'contract.json',json.dumps(contract,indent=2)+'\n')
        inventory=read(OLD/'dependency_inventory.json')
        inventory['runtime_tree_sha256']={str(p.relative_to(ROOT/'runtime')):sha(p) for p in (ROOT/'runtime').rglob('*') if p.is_file()}
        replace(ROOT/'dependency_inventory.json',json.dumps(inventory,indent=2)+'\n')
        evidence=dict(parent_release_manifest_sha256=sha(OLD/'release_manifest.json'),
            checker_validation_sha256=sha(OUT/'checker_validation.json'),
            algorithm_binaries_acceptance_budgets_and_terminal_bytes_unchanged=True,
            ctime_exception_installed=False,historical_failures_unchanged=True,
            new_native_or_STA_calls=0,full_method_confirmation=False)
        replace(ROOT/'execution_evidence.json',json.dumps(evidence,indent=2)+'\n')
        write(ROOT/'owner_identity_revision.json',dict(parent='current_sta_cp1r4',
            changed_runtime_files=changed,added_runtime_files=added,source_sha256=plan['source_sha256'],evidence=evidence))
        replace(ROOT/'README.md', '''# Current-STA confirmation CP1r5

Separate frozen CP1r4 successor. The independent checker reconciles only the documented owner registration transition: preparation bytes plus runtime_config and its source digest must reconstruct the actual execution-sealed registration exactly. The runtime bytes must also match the parent's source seal. Other changes fail. This does not adopt failed candidates or rewrite historical receipts. No LSTM-specific ctime exception is installed.

All algorithm runtime files, native binaries, search scopes, physical Tdel, budgets, acceptance, terminal selection and phase guards retain CP1r4 bytes/rules. The helper is stdlib-only. Three actual owner records and adversarial mutations validate the new expression; these are checker tests, not new full confirmations or benefits. Original package and dependencies remain immutable. Source reconstruction/admission is recorded separately before prospective execution.

Use check/run-arm with separately registered matched inputs. Complete source/request/FULL/STA/vector/physical and pair checks remain required. Record measured full command fees and every failure. TPU-OS is another known dataflow/netlist in the same TPU family and two-layer architecture, not a new architecture. Submission07 remains independently reviewable. No whole-research date/call/matrix stopping condition.
''')
        manifest=dict(release_id='current_sta_cp1r5',status='fixed_confirmation_source',
            public_evidence_base='9734eee',subsequent_public_evidence='279bdb4',
            parent_release_manifest_sha256=sha(OLD/'release_manifest.json'),
            runtime_files=len(artifact['sha256'])+1,changed_runtime_files=changed,added_runtime_files=added,
            fixed_configuration_acceptance_and_terminal_unchanged=True,
            confirmation_results_available=False,executable_modes=parent['executable_modes'],
            files_sha256={str(p.relative_to(ROOT)):sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p!=ROOT/'release_manifest.json'})
        replace(ROOT/'release_manifest.json',json.dumps(manifest,indent=2)+'\n')
        assert all(sha(ROOT/p)==h for p,h in manifest['files_sha256'].items())
        assert all(sha(OLD/p)==h for p,h in parent['files_sha256'].items())
        assert os.access(ROOT/'runtime/seccomp_thread_guard',os.X_OK)
        for name in ['release_manifest.json','contract.json','owner_identity_revision.json','execution_evidence.json','README.md']:
            shutil.copyfile(ROOT/name,OUT/name)
        for p in ROOT.rglob('*'):
            if p.is_file():p.chmod(p.stat().st_mode & ~0o222)
            elif p.is_dir():p.chmod(0o555)
        ROOT.chmod(0o555)
        write(OUT/'completion.json',dict(passed=True,release=str(ROOT),
            release_manifest_sha256=sha(ROOT/'release_manifest.json'),original_CP1r4_preserved=True,
            changed_runtime_files=changed,added_runtime_files=added,
            algorithm_fixed_configuration_unchanged=True,new_native_or_STA_calls=0,
            complete_freeze_scope_seconds=time.monotonic()-started,
            public_reconstruction_pending=True,complete_confirmation_pending=True,
            source_sha256=plan['source_sha256']))


if __name__=='__main__':main()
