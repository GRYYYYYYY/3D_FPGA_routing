#!/usr/bin/env python3
"""Seal measured outcomes, implementation snapshots and preserved historical evidence."""
from pathlib import Path
import shutil
import subprocess

from lazagna_common import ROOT,sha256,utc,write_json
from three_baseline_common import read

BASE=ROOT/'results/h3d_delay_20261027_v2'


def main():
    assert not (BASE/'finalization.json').exists()
    validation=read(BASE/'validation.json'); analysis=read(BASE/'analysis.json')
    assert validation['passed'] and analysis['registered']==94
    assert validation['full_and_audited']==analysis['success']
    assert all(e['legacy_route_equal'] and e['legacy_cpd_equal'] for e in analysis['equivalence'])
    for phase in ['pilot','main','serial']:assert read(BASE/(phase+'_state.json'))['stage']=='finished'
    for p,h in read(BASE/'source_lock.json')['protected'].items():assert sha256(ROOT/p)==h,p
    build_dir=Path(read(BASE/'protocol.json')['binary']).parent
    build=read(build_dir/'manifest.json')
    assert sha256(build_dir/'vpr')==build['binary_sha256']
    diff=subprocess.check_output(['git','diff','--binary'],cwd=ROOT/'vendor/vtr',text=True).strip()
    assert diff==(build_dir/'changes.patch').read_text()
    for p,h in build['new_source_sha256'].items():assert sha256(ROOT/'vendor/vtr'/p)==h
    assert 'Ran 28 tests' in (BASE/'python_tests.log').read_text()
    assert (BASE/'python_tests.log').read_text().rstrip().endswith('OK')
    assert '250 directed weighted graphs' in (BASE/'delay_search_test.log').read_text()
    sources=['scripts/run_h3d_delay_study.py','scripts/run_h3d_delay_v2.py',
        'scripts/validate_h3d_delay_study.py','scripts/analyze_h3d_delay_study.py',
        'scripts/finalize_h3d_delay_study.py','scripts/analyze_h3d_critical_paths.py',
        'tests/test_delay_search.cpp','docs/延迟引导优化_2026-10-27.md']
    snapshots={}
    for p in sources:
        snapshot=BASE/'implementation'/p;snapshot.parent.mkdir(parents=True,exist_ok=True)
        assert not snapshot.exists()
        shutil.copyfile(ROOT/p,snapshot)
        snapshots[p]=dict(snapshot=str(snapshot.relative_to(ROOT)),sha256=sha256(snapshot))
    # A redirected completion message changes this log after the manifest is
    # written. It is console output, never immutable experimental evidence.
    files=set(BASE.glob('*.json'))|{p for p in BASE.glob('*.log') if p.name!='finalize.log'}|set((BASE/'audits').glob('*.json'))
    for p,h in analysis['reference_bindings'].items():
        assert sha256(p)==h,p
        files.add(Path(p))
    attempts=[]
    for base in [ROOT/'results/h3d_delay_20261027',BASE]:
        files.update(base.glob('*.json'))
        for p in (base/'runs').glob('*/result.json'):
            result=read(p);receipt=p.parent/'manifest.json'
            assert read(receipt)['status'] in ('completed','failed','timeout')
            files.update([p,receipt]);attempts.append(result)
            for record in result['outputs'].values():
                assert sha256(record['path'])==record['sha256']
                files.add(Path(record['path']))
    assert len(attempts)==100
    files.update(build_dir.rglob('*'))
    evidence={str(p.relative_to(ROOT)):sha256(p) for p in sorted(files) if p.is_file()}
    write_json(BASE/'finalization.json',dict(utc=utc(),status='completed',v2_registered=94,
        v2_attempted=94,v2_full_and_independently_audited=validation['full_and_audited'],
        prior_pilot_attempted=6,prior_pilot_assertion_failures=2,prior_pilot_full_and_independently_audited=4,
        all_attempts=len(attempts),historical_files_unchanged=validation['frozen_files_unchanged'],
        current_build_matches_archive=True,implementation_snapshots=snapshots,evidence_sha256=evidence,
        excluded_live_console_logs=['results/h3d_delay_20261027_v2/finalize.log'],
        limitations='Single placement seed and selected W100 diagnostic subset. No claim of general CPD advantage or numerical superiority over paper-era LaZagna.'))
    print('Sealed',len(evidence),'evidence files,',len(snapshots),'implementation snapshots',flush=True)


if __name__=='__main__':main()
