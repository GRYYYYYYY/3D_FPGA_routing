"""Match only completed full native/domain admissions; never assemble timing."""
import fcntl
import time
import traceback
from pathlib import Path
from retained_prefix_workflow import D,read,write,route_body
from recovery_prefix_v1 import Evidence
from endpoint_timing_policy_streaming_v2 import compare


def main():
    root=D/'LSTM_domain_whole_admission_03'
    output=root/'pair'
    assert not output.exists()
    with (D/'critical_scope_runner.lock').open('r') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        output.mkdir();started=time.monotonic();e=Evidence()
        plan=read(root/'execution_plan.json');e.bind(root/'execution_plan.json');e.verify(plan['source_sha256'])
        try:
            native_path=D/'LSTM_necessary_readonly_02/native_raw/completion.json'
            domain_path=root/'raw/completion.json'
            e.bind(native_path);e.bind(domain_path)
            n,d=read(native_path),read(domain_path)
            assert n['passed'] and n['quality_admitted'] and d['passed'] and d['quality_admitted']
            for row in [n,d]:
                for field in ['initial','final']:
                    state=Path(row[field]['state']);run=Path(row[field]['run'])
                    for p in [state/'endpoint_vector.json',run/'packed.net',run/'placed.place',run/'routed.route']:
                        e.bind(p,row['source_sha256'][str(p.resolve())])
                    assert route_body(run/'routed.route')==row[field]['route_body_sha256']
            # Freshly rehash actual per-arm payloads under the serial lock;
            # graph counts or a shared XML path are insufficient to match them.
            payloads={}
            for arm,row in [('native',n),('domain',d)]:
                joint=Path(plan[arm+'_target']['case'])/'flow/resource_flow/joint_graph_indexes'
                payloads[arm]={name:e.bind(joint/name,digest) for name,digest in row['graph_payload_sha256'].items()}
            roots_match=all(n['initial'][k]==d['initial'][k] for k in
                            ['route_body_sha256','packed_sha256','placed_sha256','vector_semantic_sha256','constraints_sha256'])
            graphs_match=payloads['native']==payloads['domain']
            initial_vectors=compare(read(Path(n['initial']['state'])/'endpoint_vector.json'),read(Path(d['initial']['state'])/'endpoint_vector.json'))
            final_vectors=compare(read(Path(n['final']['state'])/'endpoint_vector.json'),read(Path(d['final']['state'])/'endpoint_vector.json'))
            assert initial_vectors['compatible'] and final_vectors['compatible']
            write(output/'initial_vectors.json',initial_vectors)
            write(output/'final_vectors.json',final_vectors)
            matched=roots_match and graphs_match
            delta={k:d['quality']['resources'][k]-n['quality']['resources'][k] for k in ['wirelength','SB_pairs','CB_sources']}
            delta['CPD_ns']=d['quality']['CPD_ns']-n['quality']['CPD_ns']
            e.unchanged()
            row=dict(passed=True,status='matched_supplementary_complete_quality_pair' if matched else 'complete_roles_admitted_but_actual_pair_matching_failed',
                     matched_complete_quality_pair=matched,quality_admitted_roles=2,
                     identical_actual_initial_tree_and_vector=roots_match,
                     six_actual_per_arm_graph_payloads_byte_matched=graphs_match,
                     native_quality=n['quality'],domain_quality=d['quality'],
                     delta_domain_minus_native=delta if matched else None,
                     final_endpoint_summary={k:v for k,v in final_vectors.items() if k!='changes'},
                     original_native_complete_attempt_seconds=n['complete_algorithm_seconds'],
                     original_domain_complete_attempt_seconds=d['complete_algorithm_seconds'],
                     formal_complete_time_ratio=None,clean_interleaved_timing_admitted=False,
                     historical_ctime_incident_and_original_failures_retained=True,
                     known_circuit_same_architecture_family=True,new_execution_or_new_input=False,
                     original_frozen_verifier_relabelled=False,new_native_or_STA_calls=0,
                     automatic_paper_update=False,
                     qualification='Posthoc complete quality admission with one exact independently audited rejected failed-role exception. Both successful fallback and all other source/request/FULL/rawSTA/endpoint/physical checks retained. Actual initial trees, full vector and six payloads matched before any paired quality delta. Original domain attempt includes ctime incident; raw complete times remain separate, no clean overhead or assembled-time ratio.')
        except Exception:
            error=traceback.format_exc();(output/'failure.log').write_text(error)
            row=dict(passed=False,status='complete_pair_matching_failed',matched_complete_quality_pair=False,
                     quality=None,error=error,formal_complete_time_ratio=None,new_native_or_STA_calls=0)
        row.update(complete_additional_matching_seconds=time.monotonic()-started,source_sha256=e.bound)
        write(output/'completion.json',row)
        assert row['passed'],row.get('error')


if __name__=='__main__':
    main()
