"""One preregistered real P1 pack/place, with existing census and guards."""
import fcntl,hashlib,json,os,time,xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from lxml import etree
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity
import prepare_s38417_input_01 as common

U=D/'VTR_diffeq_p1_input_01'
def main():
 q=U/'queue';q.mkdir(exist_ok=False);write(q/'registration.json',dict(**process_identity(os.getpid()),plan=str(U/'registration.json'),plan_sha256=sha(U/'registration.json')));write(q/'status.json',dict(status='waiting_for_shared_serial_slot'));start=time.monotonic()
 with (D/'critical_scope_runner.lock').open() as lock:
  fcntl.flock(lock,fcntl.LOCK_EX)
  try:
   plan=read(U/'registration.json');assert all(sha(p)==h for p,h in plan['source_sha256'].items());common.ROOT=U
   env=common.environment();os.environ.clear();os.environ.update(env)
   blif=U/'inputs/diffeq.blif';sdc=U/'inputs/diffeq.sdc';pack=U/'pack_01';place=U/'place_01';binary=plan['binary']['path']
   cmd=[binary,plan['census_architecture'],str(blif),'--pack','--device','fixture','--seed','11','--num_workers','1','--clock_modeling','ideal','--route_chan_width','100','--merge_constant_generators','off','--sdc_file',str(sdc),'--net_file',str(pack/'packed.net')]
   pm=common.stage('pack_01',cmd,[Path(binary),Path(plan['census_architecture']),blif,sdc],plan)
   packed_reader=D.parents[1]/'scripts/run_flatland_pack_census.py';coordinate_reader=D.parents[1]/'scripts/validate_lazagna_vtr9_pilot.py';summary=common.reader(packed_reader,'packed_summary')(pack/'packed.net')
   selected=next(row for row in plan['devices'] if all(n/row['logical_slots'][k]<=.8 for k,n in summary['block_counts'].items()));fixture=selected['fixture']
   a=ET.parse(plan['census_architecture']).getroot();b=ET.parse(fixture['architecture']).getroot();assert all(ET.tostring(a.find(k))==ET.tostring(b.find(k)) for k in ['models','tiles','complexblocklist'])
   for k in ['graph','architecture','source_graph','source_architecture']:assert sha(fixture[k])==fixture[k+'_sha256']
   write(U/'capacity_selection.json',dict(passed=True,size=selected['size'],width=100,family='hybrid_o',actual_packed=summary,selected_model=selected,selected_fixture=fixture,logical_utilization={k:n/selected['logical_slots'][k] for k,n in summary['block_counts'].items()},selection_used_routing_QoR=False,source_sha256={str(U/'registration.json'):sha(U/'registration.json'),str(pack/'packed.net'):sha(pack/'packed.net')}))
   p1=plan['p1_binary']['path'];cmd=[p1,fixture['source_architecture'],str(blif),'--pack','--place','--device',f"controlled_{selected['size']}",'--route_chan_width','100','--num_workers','1','--seed','21','--clock_modeling','ideal','--verify_file_digests','off','--read_rr_graph',fixture['source_graph'],'--timing_report_npaths','0','--net_file',str(place/'packed.net'),'--place_file',str(place/'placed.place'),'--sdc_file',str(sdc)]
   for k,v in plan['p1_options'].items():cmd.extend([k,str(v)])
   cmd.extend(['--partition_post_pack','--soft_partitioning','init_place'])
   lm=common.stage('place_01',cmd,[Path(p1),Path(fixture['source_architecture']),Path(fixture['source_graph']),blif,sdc],plan)
   part=read(place/'triton_evidence/manifest.json');assert part['returncode']==0 and part['output_valid']
   actual=common.reader(packed_reader,'packed_summary')(place/'packed.net');assert actual['semantic_sha256']==summary['semantic_sha256'] and actual['blocks']==summary['blocks']
   coords=common.reader(coordinate_reader,'placements')(place/'placed.place');names=[x.get('name') for x in etree.parse(str(place/'packed.net')).getroot().findall('block')];assert len(names)==len(set(names))==len(coords)==actual['blocks'] and set(names)==set(coords) and len(set(coords.values()))==len(coords)
   assert all(0<=v[0]<selected['size'] and 0<=v[1]<selected['size'] and v[2]>=0 and v[3] in [0,1] for v in coords.values())
   physical=dict(architecture=Path(fixture['architecture']),graph=Path(fixture['graph']),circuit=blif,packed=place/'packed.net',placement=place/'placed.place',sdc=sdc);physical={k:dict(path=str(p),bytes=p.stat().st_size,sha256=fixture[k+'_sha256'] if k in ['graph','architecture'] else sha(p)) for k,p in physical.items()}
   files=[Path(__file__).resolve(),U/'registration.json',U/'capacity_selection.json',packed_reader,coordinate_reader,place/'triton_evidence/manifest.json']
   for n in ['pack_01','place_01']:files += [U/n/f for f in ['registration.json','execution_completion.json','supervision.json','measurement/completion.json','measurement/stdout.log']]
   bindings={str(p):sha(p) for p in files};write(U/'packing_provenance.json',dict(format='derived_upstream_receipts_v1',status='completed',command=cmd,outputs={'packed.net':physical['packed'],'placed.place':physical['placement']},source_sha256=bindings,historical_manifest_rewritten=False,qualification='Actual P1 partitioned placement and matched pack census; benchmark SDC, no routing admission.'))
   write(U/'completion.json',dict(passed=True,status='actual_P1_upstream_input_preparation_verified',physical_files=physical,actual_packed=actual,actual_layout=dict(placed_blocks=len(coords),coordinate_semantic_sha256=hashlib.sha256(json.dumps([[n,*coords[n]] for n in sorted(coords)],separators=(',',':')).encode()).hexdigest(),layer_block_counts=dict(Counter(v[3] for v in coords.values()))),costs=[dict(stage='pack_01',complete_command_seconds=pm['complete_command_wall_seconds']),dict(stage='place_01',complete_command_seconds=lm['complete_command_wall_seconds'])],source_sha256={**bindings,str(U/'packing_provenance.json'):sha(U/'packing_provenance.json')},route_quality_admitted=False,route_queries=0,explicit_SDC=True,application_timing_claim=False,qualification='Different public sequential circuit, actual P1 layout, existing Hybrid-O family. Fixed 80% capacity choice prior to routing; no reroll or QoR selection.'))
   write(q/'completion.json',dict(passed=True,status='input_preparation_terminal',complete_queue_seconds=time.monotonic()-start,route_queries=0));write(q/'status.json',dict(status='terminal'));print(json.dumps(dict(passed=True,size=selected['size'],layers=dict(Counter(v[3] for v in coords.values())))))
  except BaseException as error:
   write(q/'completion.json',dict(passed=False,status='input_preparation_failed',error=repr(error),complete_queue_seconds=time.monotonic()-start,automatic_retry=False));write(q/'status.json',dict(status='terminal_reconciliation_required'));raise
if __name__=='__main__':main()
