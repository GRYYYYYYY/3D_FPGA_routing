"""Materialize dynamic native analyses as physically audited routing states.

The new manifest labels a forked child explicitly: child time is never silently
presented as a complete fresh VPR process or complete algorithm time. A state
must reference the final pool/cache input seal before archival publication.
"""
import os
import inspect
from pathlib import Path
import shutil
import sys
import time
from retained_prefix_workflow import D,read,write,sha,route_body
from endpoint_timing_policy import load
from full_route_graph_cache import FullRouteGraphCache
from run_native_scope_policy_v4 import run_dir

ROOT=D.parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import flatland_benchmark as study
from run_vpr import parse_metrics


def file_stat(path):
    s=Path(path).stat();return [s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns]


class PoolStateEvaluator:
    """Use one immutable graph cache and one owner for complete candidate states."""
    def __init__(self,pool,initial_state,graph_cache,directory):
        self.pool=pool;self.pool_module=Path(inspect.getfile(type(pool))).resolve();self.initial_state=Path(initial_state).resolve();self.source=run_dir(self.initial_state)
        self.directory=Path(directory).resolve();self.directory.mkdir(exist_ok=False);self.started=time.monotonic();self.states=[];self.closed=False
        r=read(pool.directory/'registration.json');assert r['runtime_libraries_resolved_before_start']
        self.command=list(r['command']);self.net=Path(self.command[self.command.index('--net_file')+1]);self.place=Path(self.command[self.command.index('--place_file')+1]);self.graph=Path(self.command[self.command.index('--read_rr_graph')+1]);self.constraints=read(self.initial_state/'endpoint_vector.json')['constraints_sha256']
        assert sha(self.net)==sha(self.source/'packed.net') and sha(self.place)==sha(self.source/'placed.place')
        self.cache=FullRouteGraphCache(self.graph,graph_cache);cc=read(self.cache.directory/'completion.json');parent=self.cache.g.directory;pc=read(parent/'completion.json')
        self.cache_hashes={str(self.cache.directory/n):h for n,h in cc['payload_sha256'].items()};self.cache_hashes.update({str(parent/n):h for n,h in pc['payload_sha256'].items()});self.cache_hashes.update({str(self.cache.directory/'completion.json'):sha(self.cache.directory/'completion.json'),str(parent/'completion.json'):sha(parent/'completion.json')});self.cache_stats={p:file_stat(p) for p in self.cache_hashes}
        write(self.directory/'registration.json',dict(initial_state=str(self.initial_state),pool_registration=str(pool.directory/'registration.json'),pool_registration_sha256=sha(pool.directory/'registration.json'),graph_cache_receipt=self.cache.receipt,cache_payload_sha256=self.cache_hashes,constraints_sha256=self.constraints,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),self.pool_module,self.initial_state/'completion.json',self.initial_state/'endpoint_vector.json']},qualification='Algorithm-facing native state schema with effective child options and separate parent/child/whole-cost levels. Caller still selects targets and decides acceptance. Final publication requires this evaluator input seal and pool completion.'))

    @staticmethod
    def _body(path):
        try:return route_body(path)
        except AssertionError:return None

    def _check_inputs(self):
        self.pool._require_static()
        assert all(file_stat(p)==s for p,s in self.cache_stats.items()),'Immutable physical graph cache changed'

    def evaluate(self,route,output,*,physical_reference=None,reuse=True,native_observation=None):
        """Return native FULL/STA, actual resource metrics and exact vector gates."""
        assert not self.closed;self._check_inputs();started=time.monotonic();route=Path(route).resolve();b=Path(output).resolve();b.mkdir(exist_ok=False);native=self.pool.analyze(route,echo=True,reuse=reuse) if native_observation is None else native_observation;assert native['static_identity']==self.pool.identity and native['route_sha256']==sha(route);assert all(sha(p)==h for p,h in native['artifact_sha256'].items());rd=b/'runs/state';rd.mkdir(parents=True)
        before=sha(route);job=Path(native['job']);native_dir=Path(native['native_directory']);options=native.get('native_options',dict(operation='analysis'));repair=options['operation']=='repair';query_count=sum(l.startswith('QUERY ') for l in (native_dir/'joint_native.log').read_text().splitlines()) if repair and (native_dir/'joint_native.log').exists() else 0
        write(b/'registration.json',dict(status='materializing_native_state',candidate_route=str(route),candidate_sha256=before,native_receipt=str(job/'completion.json'),native_receipt_sha256=sha(job/'completion.json'),pool_identity=self.pool.identity,source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),self.pool_module,self.directory/'registration.json']},requires_final_input_seal=str(self.directory/'input_seal.json'),qualification='Native analysis may be an explicitly reused exact observation. No native creation time is borrowed for reuse. State remains private until the pool/cache final seal passes.'))
        for name,src in [('packed.net',self.net),('placed.place',self.place),('routed.route',route)]:shutil.copy2(src,rd/name)
        for name in ['stdout.log','stderr.log','native_sta_frontier.jsonl','native_sta_frontier.jsonl.constraints.echo','timing_graph.full_precision.echo','joint_native.log','vertical_domain.log']:
            if (native_dir/name).is_file():shutil.copy2(native_dir/name,rd/name)
        vector=load(rd/'native_sta_frontier.jsonl') if native['passed'] else None
        metrics=parse_metrics((rd/'stdout.log').read_text(errors='replace')) if (rd/'stdout.log').exists() else {}
        command=list(self.command);command[command.index('--route_file')+1]=str(job/'routed.route')
        manifest=dict(schema_version=2,name='state',status='completed' if native['passed'] else 'timeout' if native['timed_out'] else 'failed',command=command,command_semantics='Effective child VPR options; parent executed its registered command, forked before route LOAD, and applied the explicit candidate route override. No separate exec of these child options is claimed.',cwd=str(native_dir),shared_inputs={p:dict(sha256=h,stat_identity=self.pool.input_stats[p]) for p,h in self.pool.inputs.items()},private_input_sha256={str(rd/n):sha(rd/n) for n in ['packed.net','placed.place','routed.route']},metrics=metrics,environment=dict(VPR_H3D_MODE='off',OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1'),runtime_environment_digest=self.pool.environment_digest,execution_scope='preloaded_native_child',returncode=native['native_exit_code'],native_signal=native['native_signal'],native_child_seconds=None if native_observation is not None else native['native_child_seconds'],consumed_already_executed_worker_receipt=native_observation is not None,native_options=options,native_worker_creation_child_seconds=native['native_child_seconds'] if native_observation is not None else None,wall_seconds=None,complete_single_configuration_seconds=None,parent_provenance=dict(pool=str(self.pool.directory),epoch_pid=native['epoch_pid'],epoch_start_ticks=native['epoch_start_ticks'],child_pid=native['child_pid'],receipt=native['receipt']),native_reused=native['reused'],original_creation_time_borrowed=False,outputs={n:dict(sha256=sha(rd/n),bytes=(rd/n).stat().st_size) for n in ['packed.net','placed.place','routed.route','stdout.log'] if (rd/n).exists()})
        write(rd/'manifest.json',manifest);write(rd/'pair_check.json',dict(passed=sha(rd/'packed.net')==sha(self.net) and sha(rd/'placed.place')==sha(self.place),scope='Exact static packing and placement loaded into parent before every private child.'))
        checks=dict(native_complete=native['passed'],native_FULL=bool(metrics.get('native_full_check_passed')),native_success_reported=bool(metrics.get('routing_success_reported')),candidate_unchanged=sha(route)==before==sha(rd/'routed.route'),native_precision_echo=(rd/'timing_graph.full_precision.echo').is_file(),constraints_unchanged=vector is not None and vector['constraints_sha256']==self.constraints)
        if vector is not None:checks['reported_CPD_matches_full_precision']=float(format(vector['cpd_s']*1e9,'.6g'))==metrics.get('critical_path_ns');write(b/'endpoint_vector.json',vector)
        audit_start=time.monotonic();audit_reused=False
        if all(checks.values()):
            if physical_reference is not None:
                reference=run_dir(Path(physical_reference));expected=read(reference/'independent_audit.json');assert expected['audit']['passed'];assert sha(reference/'routed.route')==before and sha(reference/'packed.net')==sha(self.net) and sha(reference/'placed.place')==sha(self.place)
                rm=read(reference/'manifest.json');rg=Path(rm['command'][rm['command'].index('--read_rr_graph')+1]);assert rg==self.graph and rm['shared_inputs'][str(rg)]['sha256']==self.cache.g.receipt['graph_sha256']
                shutil.copy2(reference/'independent_audit.json',rd/'independent_audit.json');audit_reused=True;write(b/'physical_audit_reuse.json',dict(passed=True,reference=str(reference/'independent_audit.json'),reference_sha256=sha(reference/'independent_audit.json'),exact_route_sha256=before,graph_sha256=self.cache.g.receipt['graph_sha256'],qualification='Same actual route, graph, packing and placement; exact existing physical audit copied with explicit provenance, not a new execution.'))
            else:
                previous_base=study.BASE;previous_reader=study.cr.read_graph_evidence;previous_records=study.cr.graph_records;study.BASE=b;study.cr.read_graph_evidence=self.cache.evidence
                try:
                    try:
                        result=study.audit_batch({'fixture':{'original_graph':str(self.graph)}},[manifest],b/'independent_native_analysis_audit.json');assert result['passed'] and result['legal_count']==1
                    except Exception as error:
                        write(b/'physical_audit_failure.json',dict(passed=False,error_type=type(error).__name__,error=str(error)))
                finally:study.BASE=previous_base;study.cr.read_graph_evidence=previous_reader;study.cr.graph_records=previous_records
            checks['physical_audit']=(rd/'independent_audit.json').exists() and read(rd/'independent_audit.json')['audit']['passed'] and not(b/'physical_audit_failure.json').exists()
        else:checks['physical_audit']=False
        audit_elapsed=time.monotonic()-audit_start
        self._check_inputs();write(rd/'analysis_gate.json',dict(passed=all(checks.values()),checks=checks,requires_final_input_seal=str(self.directory/'input_seal.json')))
        result=dict(status='pooled_native_analysis_terminal',passed=all(checks.values()),accepted=None,run=str(rd),native_analysis_calls=0 if native['reused'] or native_observation is not None else 1,consumed_already_executed_worker_receipt=native_observation is not None,native_transaction_calls=0 if native_observation is not None or not repair else 1,native_worker_query_count=query_count,route_search_calls=0 if native_observation is not None else query_count,cpd_ns=metrics.get('critical_path_ns'),full_precision_cpd_s=None if vector is None else vector['cpd_s'],endpoints=None if vector is None else len(vector['endpoint_ids']),process_status=manifest['status'],route_body_sha256=self._body(rd/'routed.route'),observer_binary_sha256=self.pool.binary_sha256,execution_scope='preloaded_native_child',native_reused=native['reused'],physical_audit_reused=audit_reused,timing=dict(native_worker_creation_child_seconds=native['native_child_seconds'] if native_observation is not None else None,native_child_seconds=None if native_observation is not None else native['native_child_seconds'],native_parent_startup_allocation=None,independent_audit_seconds=audit_elapsed,complete_evaluation_request_seconds=time.monotonic()-started,complete_single_configuration_algorithm_seconds=None),requires_final_input_seal=str(self.directory/'input_seal.json'),timing_echo_sha256=sha(rd/'timing_graph.full_precision.echo') if (rd/'timing_graph.full_precision.echo').exists() else None,checks=checks,qualification='A repair worker receipt observes its original input and carries private candidate sidecars; it does not validate those candidate trees. Consuming a completed receipt records no new native query or borrowed time. Native/physical/vector gate for a private candidate, not an acceptance decision. Publication requires the declared pool/cache final input seal. Child time is not standalone VPR process time; parent startup, candidate preparation, failures and final sealing remain in whole workflow accounting.')
        write(b/'completion.json',result);self.states.append(str(b));write(self.directory/'states.json',self.states);return result

    def close(self):
        """Finalize one cohort without modifying already hashed intermediate states."""
        if self.closed:return
        self.pool.close();pc=read(self.pool.directory/'completion.json');checks={p:sha(p)==h and file_stat(p)==self.cache_stats[p] for p,h in self.cache_hashes.items()};passed=pc['passed'] and all(checks.values());write(self.directory/'input_seal.json',dict(passed=passed,pool_completion=str(self.pool.directory/'completion.json'),pool_completion_sha256=sha(self.pool.directory/'completion.json'),cache_checks=checks,source_sha256={str(p):sha(p) for p in [self.directory/'registration.json',self.directory/'states.json',Path(__file__).resolve()]},qualification='Final source epoch gate. Per-state completion files remain immutable so downstream current-state provenance is not invalidated.'))
        self.closed=True;write(self.directory/'completion.json',dict(passed=passed,states=self.states,complete_component_workflow_seconds=time.monotonic()-self.started,complete_single_configuration_algorithm_seconds=None,source_sha256={str(p):sha(p) for p in [self.directory/'input_seal.json',self.directory/'states.json']},qualification='Native child, materialization and physical audit workflow. Initial routing/whole algorithm costs excluded.'))
        assert passed,'Pool/cache final input epoch failed; private states must not be published'
