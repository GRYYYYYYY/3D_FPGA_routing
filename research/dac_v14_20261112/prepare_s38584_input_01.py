"""One registered pack/place input, reusing existing measured execution and readers."""
import fcntl
import hashlib
import json
import os
import shutil
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from lxml import etree
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity
from measure_process_tree_v1 import measure
from finalize_elliptic_input_01 import reader
from cp1r5_elliptic_cohort_01 import environment

ROOT=D/'VTR_s38584_input_01'


def stage(name, command, inputs, plan):
    out=ROOT/name;out.mkdir()
    start=time.monotonic()
    bindings={str(p):sha(p) for p in inputs}
    write(out/'registration.json',dict(command=command,source_sha256=bindings,
        registered_at=datetime.now(timezone.utc).isoformat(),timeout_seconds=3600,
        memory_limit_bytes=68719476736,route_queries=0))
    write(ROOT/'queue/status.json',dict(status='running_'+name,phase=name))
    command=[sys.executable,'-B',plan['supervisor'],'--receipt',str(out/'supervision.json'),
        '--seconds','3600','--','/usr/bin/prlimit','--as=68719476736','--',*command]
    prep=time.monotonic()-start
    cwd=Path.cwd();os.chdir(out)
    try:measurement=measure(command,out/'measurement')
    finally:os.chdir(cwd)
    supervision=read(out/'supervision.json')
    write(out/'execution_completion.json',dict(execution_ended=True,
        returncode=measurement['returncode'],passed=measurement['passed'] and supervision['passed'],
        complete_upstream_command_seconds=measurement['complete_command_wall_seconds'],
        input_binding_seconds=prep,route_queries=0,quality_admitted=False))
    assert not measurement['live_descendants_after_command_exit'] and not supervision['residual_descendants']
    assert measurement['passed'] and supervision['passed'], 'Preserve failed preparation; no automatic rerun or resizing'
    assert 'VPR succeeded' in (out/'measurement/stdout.log').read_text()
    return measurement


def main():
    queue=ROOT/'queue';queue.mkdir(exist_ok=False)
    write(queue/'registration.json',dict(**process_identity(os.getpid()),plan=str(ROOT/'registration.json'),
        plan_sha256=sha(ROOT/'registration.json')))
    write(queue/'status.json',dict(status='waiting_for_shared_serial_slot'))
    started=time.monotonic()
    with (D/'critical_scope_runner.lock').open() as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        try:
            plan=read(ROOT/'registration.json')
            assert all(sha(p)==h for p,h in plan['source_sha256'].items())
            env=environment();os.environ.clear();os.environ.update(env)
            blif=ROOT/'inputs/s38584.blif';sdc=ROOT/'inputs/s38584.sdc'
            pack=ROOT/'pack_01';place=ROOT/'place_01';binary=plan['binary']['path']
            command=[binary,plan['census_architecture'],str(blif),'--pack','--device','fixture',
                '--seed','11','--num_workers','1','--clock_modeling','ideal','--route_chan_width','100',
                '--merge_constant_generators','off','--sdc_file',str(sdc),'--net_file',str(pack/'packed.net')]
            pm=stage('pack_01',command,[Path(binary),Path(plan['census_architecture']),blif,sdc],plan)
            packed_reader=D.parents[1]/'scripts/run_flatland_pack_census.py'
            coordinate_reader=D.parents[1]/'scripts/validate_lazagna_vtr9_pilot.py'
            summary=reader(packed_reader,'packed_summary')(pack/'packed.net')
            selected=next(row for row in plan['devices'] if all(n/row['logical_slots'][k]<=.8
                for k,n in summary['block_counts'].items()))
            fixture=selected['fixture']
            a=ET.parse(plan['census_architecture']).getroot();b=ET.parse(fixture['architecture']).getroot()
            assert all(ET.tostring(a.find(k))==ET.tostring(b.find(k)) for k in ['models','tiles','complexblocklist'])
            write(ROOT/'capacity_selection.json',dict(passed=True,size=selected['size'],width=100,family='hybrid_o',
                actual_packed=summary,selected_model=selected,selected_fixture=fixture,
                logical_utilization={k:n/selected['logical_slots'][k] for k,n in summary['block_counts'].items()},
                selection_used_routing_QoR=False,source_sha256={str(ROOT/'registration.json'):sha(ROOT/'registration.json'),str(pack/'packed.net'):sha(pack/'packed.net')}))
            # Independent copies; do not alter metadata of the completed packed source.
            private=ROOT/'inputs/packed.net';shutil.copyfile(pack/'packed.net',private)
            command=[binary,fixture['architecture'],str(blif),'--place','--device','fixture',
                '--route_chan_width','100','--num_workers','1','--seed','21','--clock_modeling','ideal',
                '--verify_file_digests','off','--read_rr_graph',fixture['graph'],'--timing_report_npaths','0',
                '--net_file',str(private),'--place_file',str(place/'placed.place'),
                '--merge_constant_generators','off','--sdc_file',str(sdc)]
            for kind in ['graph','architecture']:assert sha(fixture[kind])==fixture[kind+'_sha256']
            lm=stage('place_01',command,[Path(binary),Path(fixture['architecture']),Path(fixture['graph']),blif,sdc,private],plan)
            assert reader(packed_reader,'packed_summary')(private)==summary
            coords=reader(coordinate_reader,'placements')(place/'placed.place')
            names=[x.get('name') for x in etree.parse(str(private)).getroot().findall('block')]
            assert len(names)==len(set(names))==len(coords)==summary['blocks'] and set(names)==set(coords)
            assert len(set(coords.values()))==len(coords)
            assert all(0<=v[0]<selected['size'] and 0<=v[1]<selected['size'] and v[2]>=0 and v[3] in [0,1] for v in coords.values())
            physical=dict(architecture=Path(fixture['architecture']),graph=Path(fixture['graph']),circuit=blif,
                packed=private,placement=place/'placed.place',sdc=sdc)
            physical={k:dict(path=str(p),bytes=p.stat().st_size,sha256=fixture[k+'_sha256'] if k in ['graph','architecture'] else sha(p)) for k,p in physical.items()}
            source_files=[Path(__file__).resolve(),ROOT/'registration.json',ROOT/'capacity_selection.json',packed_reader,coordinate_reader]
            for stage_name in ['pack_01','place_01']:
                source_files += [ROOT/stage_name/n for n in ['registration.json','execution_completion.json','supervision.json','measurement/completion.json','measurement/stdout.log']]
            bindings={str(p):sha(p) for p in source_files}
            write(ROOT/'packing_provenance.json',dict(format='derived_upstream_receipts_v1',status='completed',
                command=command,outputs={'packed.net':physical['packed'],'placed.place':physical['placement']},
                source_sha256=bindings,historical_manifest_rewritten=False,
                qualification='Derived from actual recorded pack/place commands; explicit benchmark clock constraint, not an external application requirement. No routing admission.'))
            write(ROOT/'completion.json',dict(passed=True,status='actual_upstream_input_preparation_verified',
                physical_files=physical,actual_packed=summary,
                actual_layout=dict(placed_blocks=len(coords),coordinate_semantic_sha256=hashlib.sha256(json.dumps([[n,*coords[n]] for n in sorted(coords)],separators=(',',':')).encode()).hexdigest(),layer_block_counts=dict(Counter(v[3] for v in coords.values()))),
                costs=[dict(stage='pack_01',complete_command_seconds=pm['complete_command_wall_seconds']),dict(stage='place_01',complete_command_seconds=lm['complete_command_wall_seconds'])],
                source_sha256={**bindings,str(ROOT/'packing_provenance.json'):sha(ROOT/'packing_provenance.json')},
                route_quality_admitted=False,route_queries=0,explicit_SDC=True,application_timing_claim=False,
                qualification='Distinct public sequential circuit, one actual fresh placement, existing Hybrid-O architecture family. Size selected before routing from measured packing and fixed80%capacity rule including already audited n25 fixtures. Upstream internal STA and costs are separate from subsequent full routing. Do not resize or reroll after QoR.'))
            write(queue/'completion.json',dict(passed=True,status='input_preparation_terminal',complete_queue_seconds=time.monotonic()-started,route_queries=0))
            write(queue/'status.json',dict(status='terminal'))
            print(json.dumps(dict(passed=True,size=selected['size'],blocks=summary['block_counts'],layers=dict(Counter(v[3] for v in coords.values())))))
        except BaseException as error:
            write(queue/'completion.json',dict(passed=False,status='input_preparation_failed',error=repr(error),complete_queue_seconds=time.monotonic()-started,automatic_retry=False))
            write(queue/'status.json',dict(status='terminal_reconciliation_required'));raise


if __name__=='__main__':main()
