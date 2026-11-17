"""Narrow actual timing-worker schema reconciliation; reuse all original raw gates."""
import argparse
import inspect
import textwrap
from pathlib import Path
import admit_cp1r6_diffeq_p1_base_01 as prior
from retained_prefix_workflow import D, read

ROOT = D/'DIFFEQ_P1_complete_admission_01'
BUILD = D/'resource_domain_stage_01'
BINARY_SHA = '25f24fc2d606dc2d551c460f89b8cffbbcd6e7b7642c4078a199007bea3735c2'
SOURCE_SHA = '4f91fccef49a0b147639799d968df855056db5a30052caf2a2ca6738f1ab3ce4'
UNUSED = ('VPR_JOINT_NATIVE_SEED_ORDER', 'VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE')
RESOURCE_FIELDS = {'seed_order','domain_failure_release','crossing_reuse_enabled','crossing_domain'}
OLD = """        assert env['VPR_JOINT_NATIVE_SEED_ORDER'] == role['seed_order']
        assert env['VPR_JOINT_NATIVE_DOMAIN_FAILURE_RELEASE'] == ('1' if role['domain_failure_release'] else '0')
        if role['crossing_reuse_enabled']:
            assert self.e.bind(role['crossing_domain']) == self.e.bind(env['VPR_JOINT_NATIVE_REUSE_CROSSINGS'])
        else:assert env['VPR_JOINT_NATIVE_REUSE_CROSSINGS'] == ''"""


def check_timing_fields(name, role, manifest, descriptor):
    assert name == 'current_group'
    assert role['scope'] == 'automatic_current_group' and role['baseline'] == 'current'
    assert not (RESOURCE_FIELDS & role.keys()), 'Mixed resource/timing registration'
    assert role['objective'] == 'weighted_soft' and role['fixed_target_paths'] is False
    assert descriptor['phase'] == 'timing_repair'
    assert descriptor['files']['binary']['sha256'] == BINARY_SHA
    assert manifest['command'][0] == descriptor['files']['binary']['path']
    assert manifest['shared_inputs'][manifest['command'][0]]['sha256'] == BINARY_SHA
    env = manifest['environment']
    assert not any(k in env for k in UNUSED), 'Unexpected timing worker override'
    assert env['VPR_JOINT_NATIVE_OBJECTIVE'] == role['objective']
    assert env['VPR_JOINT_NATIVE_REQUEST'] == role['request']
    assert env['VPR_JOINT_NATIVE_REUSE_CROSSINGS'] == ''
    assert env['VPR_JOINT_NATIVE_VERTICAL_DOMAIN_TRACE'] == ''


def verify_timing_worker(audit, tx, flow, name, role, manifest):
    assert tx.is_relative_to(flow/'timing')
    registration = audit.document(tx/'registration.json')
    assert set(registration['roles']) == {'current_group'}
    descriptor = audit.document(tx/'current_group_native_inputs.json')
    check_timing_fields(name, role, manifest, descriptor)
    audit.e.bind(descriptor['runtime_config'], descriptor['runtime_config_sha256'])
    binding = audit.document(BUILD/'binding.json')
    assert binding['binary_sha256'] == BINARY_SHA
    relative = 'vpr/src/route/h3d_joint_native_repair.h'
    assert binding['source_sha256'][relative] == SOURCE_SHA
    source = BUILD/'src'/relative
    audit.e.bind(source, SOURCE_SHA)
    binary = Path(manifest['command'][0]);audit.e.bind(binary, BINARY_SHA)
    # This older timing binary does not implement the resource binary's knobs.
    # Absence is not interpreted as a fabricated resource-worker default.
    assert all(k not in source.read_text() for k in UNUSED)
    assert all(k.encode() not in binary.read_bytes() for k in UNUSED)
    worker = audit.release/'runtime/run_independent_resource_state_analysis_stream_v1.py'
    runner = audit.release/'runtime/run_registered_independent_stream_transactions_v1.py'
    execution = audit.document(tx/'execution_registration.json')
    for path in [worker,runner]:
        audit.e.bind(path, execution['source_sha256'][str(path)])
    costs = audit.document(tx/'process_costs.json')
    actual = [c for c in costs if c['tag']=='current_group_native']
    assert len(actual)==1 and actual[0]['returncode']==0
    command=actual[0]['command'];assert command[1]==str(worker)
    assert command[command.index('--inputs')+1]==str(tx/'current_group_native_inputs.json')
    assert command[command.index('--native-cases')+1]==role['request']
    assert command[command.index('--objective')+1]==role['objective']
    log=Path(manifest['cwd'])/'joint_native.log'
    audit.e.bind(log);assert log.read_text().startswith('MODE weighted_soft\n')


ORIGINAL_CLASS = prior.audit_class


def audit_class():
    parent=ORIGINAL_CLASS()
    source=textwrap.dedent(inspect.getsource(prior.raw.Audit.transaction))
    assert source.count(OLD)==1
    replacement="""        if role.get('scope') == 'automatic_current_group':
            verify_timing_worker(self, tx, flow, name, role, manifest)
        else:
"""+textwrap.indent(OLD,'    ')
    revised=source.replace(OLD,replacement)
    assert revised.replace(replacement,OLD)==source
    namespace={**prior.raw.__dict__,'verify_timing_worker':verify_timing_worker}
    exec(compile(revised,str(Path(__file__).resolve())+'::timing_schema','exec'),namespace)
    class TimingSchemaAudit(parent):
        pass
    TimingSchemaAudit.transaction=namespace['transaction']
    assert TimingSchemaAudit.state is prior.raw.Audit.state
    return TimingSchemaAudit


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--role',choices=['native','domain','pair'],required=True)
    args=parser.parse_args();prior.ROOT=ROOT;prior.audit_class=audit_class
    if args.role=='pair':prior.pair()
    else:prior.role(args.role)
