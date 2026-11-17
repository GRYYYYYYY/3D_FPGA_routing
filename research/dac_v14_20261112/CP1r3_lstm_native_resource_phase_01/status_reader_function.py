def evaluation_receipt_evidence(evaluation):
    """Read existing worker/materializer gates, without re-running native work.

    This is status evidence, not an adoption adapter or a new byte/STA audit.
    The materializer's installed-candidate manifest must remain distinguishable
    from the source LOAD that supplied its already executed callback.
    """
    evaluation=Path(evaluation);completion=evaluation/'completion.json';done=read(completion)
    receipts=[completion];checks=done.get('checks')
    if isinstance(checks,dict) and checks:
        evidence=dict(schema='original_worker_checks',passed=bool(done['passed'] and all(checks.values())),original_checks=checks)
    elif done.get('status')=='standalone_candidate_materialization_terminal':
        gate_path=evaluation/'runs/state/analysis_gate.json'
        audit_path=evaluation/'independent_native_analysis_audit.json'
        manifest_path=evaluation/'runs/state/manifest.json'
        registration_path=evaluation/'registration.json'
        receipts.extend([gate_path,audit_path,manifest_path,registration_path])
        gate=read(gate_path);audit=read(audit_path);manifest=read(manifest_path);registration=read(registration_path)
        worker=Path(registration['source_worker']);worker_completion=worker/'completion.json';exports_path=worker/'candidate_exports.json'
        receipts.extend([worker_completion,exports_path]);closed=read(worker_completion);exports=read(exports_path)
        passed=(done['passed'] and done.get('native_analysis_calls')==0
            and done.get('consumed_already_executed_worker_receipt') is True
            and all(gate.get(k) is True for k in ['passed','native_candidate_FULL_fresh_STA','physical_capacity_audit','source_restored'])
            and audit.get('passed') is True and audit.get('legal_count')==1 and audit.get('failed_count')==0
            and manifest.get('status')=='completed' and manifest.get('observed_state_kind')=='installed_candidate'
            and manifest.get('execution_scope')=='standalone_installed_candidate_callback'
            and manifest.get('native_analysis_calls_new')==0
            and manifest.get('source_worker_completion')==str(worker_completion)
            and manifest.get('metrics',{}).get('native_full_check_passed') is True
            and closed.get('passed') is True and exports.get('passed') is True and exports.get('candidate_gate_present') is True)
        evidence=dict(schema='original_installed_candidate_materialization',passed=bool(passed),
            original_analysis_gate=gate,original_independent_audit=dict(passed=audit.get('passed'),legal_count=audit.get('legal_count'),failed_count=audit.get('failed_count')),
            manifest_execution_scope=manifest.get('execution_scope'),source_worker=str(worker),
            consumed_already_executed_worker_receipt=done.get('consumed_already_executed_worker_receipt'),
            new_native_analysis_calls=done.get('native_analysis_calls'),
            complete_materialization_seconds=done.get('complete_materialization_seconds'))
    else:
        evidence=dict(schema=done.get('status'),passed=False,status_reason='Unsupported receipt schema; no validation inferred')
    assert all(p.stat().st_size<4*1024**2 for p in receipts),'Status reader consumes small gate receipts only'
    evidence['source_receipt_sha256']={str(p):sha(p) for p in receipts}
    return evidence
