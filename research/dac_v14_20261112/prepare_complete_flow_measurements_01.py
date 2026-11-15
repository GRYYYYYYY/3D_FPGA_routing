"""Freeze small-fixture validation and a matched eltwise 2x2 cost experiment."""
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
from run_native_scope_policy_v4 import run_dir

out=D/'complete_route_resource_measurements_01';out.mkdir(exist_ok=False)
configdir=out/'configs';configdir.mkdir()
binary=D/'native_resource_census_stage_01/bin/vpr'
source=run_dir(D/'native_endpoint_vector_dev_01/A0')
actual=list(read(source/'manifest.json')['command'])
tiny=list(read(D/'export_policy_tiny_01/pool/registration.json')['command'])
scripts=[D/n for n in ['run_complete_route_resource_flow_v1.py','measure_process_tree_v1.py',
    'run_seed_census_shadow_resource_repair.py','seed_census_analysis_pool_v2.py','pool_state_evaluator_v7.py',
    'current_crossing_share_selector_v2.py','current_resource_bundle_v2.py','immutable_rr_audit_cache.py',
    'full_route_graph_cache.py','endpoint_timing_policy_streaming_v2.py','multiobjective_acceptance_v2.py']]
cases={}
for circuit,base in [('tiny',tiny),('eltwise',actual)]:
    for cache in ['build_inside_flow','reusable_graph_only']:
        for mode in ['unrestricted','paired']:
            if circuit=='tiny' and (cache!='build_inside_flow' or mode!='paired'):continue
            command=list(base);command[0]=str(binary)
            if '--route' not in command:command.insert(3,'--route')
            if '--analysis' not in command:command.insert(4,'--analysis')
            if '--timing_report_npaths' not in command:command+=['--timing_report_npaths','10']
            if '--max_router_iterations' not in command:command+=['--max_router_iterations','200']
            # Match the existing A0 convergence opportunity; tiny has a small fixed default.
            if '--router_max_convergence_count' not in command:command+=['--router_max_convergence_count','2']
            static=[binary,Path(command[1]),Path(command[2])]+[Path(command[command.index(k)+1]) for k in ['--read_rr_graph','--net_file','--place_file']]
            command[command.index('--route_file')+1]='<fresh output assigned inside measured command>'
            full=D/'full_route_graph_cache_e695_01'
            if cache=='reusable_graph_only':
                fc=read(full/'completion.json');parent=Path(fc['parent_cache']);pc=read(parent/'completion.json')
                static += [full/'completion.json',parent/'completion.json']
                static += [full/n for n in fc['payload_sha256']]+[parent/n for n in pc['payload_sha256']]
            name=f'{circuit}_{cache}_{mode}'
            config=dict(circuit=circuit,cache_mode=cache,domain_mode=mode,domain_feedback=mode=='paired',
                initial_route_imported=False,route_command=command,full_graph_cache=str(full) if cache=='reusable_graph_only' else None,
                input_sha256={str(p.resolve()):sha(p) for p in [*static,*scripts]},
                declaration='Architecture, BLIF, packed netlist, placement, fixed options and binary are inputs. Every initial route is generated fresh. Only physical graph indexes may be reusable; no historical route, candidate or query results are imported.',
                memory_semantics='GNU waited-process RSS high-water and sampled simultaneous process-tree RSS/PSS; no conflation.',
                cache_semantics='Fresh-process algorithm startup. OS page cache is uncontrolled; no system cache drop.',
                development_only=True)
            path=configdir/(name+'.json');write(path,config);cases[name]=str(path)
order=['tiny_build_inside_flow_paired','eltwise_build_inside_flow_unrestricted','eltwise_build_inside_flow_paired',
       'eltwise_reusable_graph_only_paired','eltwise_reusable_graph_only_unrestricted']
assert set(order)==set(cases)
write(out/'plan.json',dict(passed=True,cases=cases,fixed_order=order,
    source_sha256={str(p):sha(p) for p in [Path(__file__).resolve(),*scripts,*map(Path,cases.values())]},
    qualification='Tiny actual pipeline validation then one fixed-order 2x2 development measurement on eltwise; neither repeats nor independent test circuits. Same roots and opportunities per arm; no best-of selection. Single observations identify overhead, not statistical speedup. Full-flow validity and matched outputs must pass before comparisons.'))
print(dict(configurations=order,plan=str(out/'plan.json')),flush=True)
