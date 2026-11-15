"""Explicit phase binaries and physical inputs for the original serial controller."""
import json,os,resource
from pathlib import Path
from retained_prefix_workflow import read,write,sha
from observe import inputs
from transact import state_view
PACKAGE=Path(__file__).resolve().parent

def package_files():
 manifest=PACKAGE/'artifact_manifest.json';record=read(manifest)
 assert record['format']=='standalone_serial_resource_controller_development_v1'
 paths=[PACKAGE/n for n in record['sha256']]
 assert all(sha(PACKAGE/n)==h for n,h in record['sha256'].items()),'Immutable package changed'
 return [manifest,*paths]

def configuration(path):
 path=Path(path).resolve();cfg=read(path)
 assert cfg['format']=='explicit_unified_phase_runtime_v1'
 assert set(cfg['phase_binaries']) in [{'resource','owner'},{'resource','owner','timing_repair','timing_observer'}]
 assert {'architecture','circuit','graph','packed','placement'}<=set(cfg['physical_files'])<= {'architecture','circuit','graph','packed','placement','sdc'}
 files=[];physical={};binaries={}
 for group,target in [('physical_files',physical),('phase_binaries',binaries),('query_engines',{}),('query_validations',{})]:
  for key,row in cfg.get(group,{}).items():
   p=(path.parent/row['path']).resolve();assert p.is_file() and sha(p)==row['sha256'],(group,key)
   if group in ['phase_binaries','query_engines']:assert os.access(p,os.X_OK)
   target[key]=p;files.append(p);cfg[group][key]=dict(row,path=str(p))
 return cfg,physical,binaries,files

def admit_controller(config,state,cache_directory):
 cfg,physical,binaries,files=configuration(config);view=state_view(state);run=view['run'];manifest=read(run/'manifest.json');command=manifest['command']
 for key,p in [('architecture',command[1]),('circuit',command[2]),('graph',command[command.index('--read_rr_graph')+1]),('packed',run/'packed.net'),('placement',run/'placed.place')]:
  assert sha(physical[key])==sha(p),('Runtime differs from source',key)
 directory=Path(cache_directory).resolve();assert sha(directory/'completion.json')==cfg['full_graph_cache_completion_sha256']
 full=read(directory/'completion.json');assert full['passed'] and full['graph_sha256']==sha(physical['graph'])
 parent=Path(full['parent_cache']);assert sha(parent/'completion.json')==full['parent_completion_sha256']
 for d in [directory,parent]:files += [d/'completion.json',*[d/n for n in read(d/'completion.json')['payload_sha256']]]
 # SDC must be present on both sides or absent on both sides.
 assert ('sdc' in physical)==('--sdc_file' in command)
 if 'sdc' in physical:assert sha(physical['sdc'])==sha(command[command.index('--sdc_file')+1])
 return files

def worker_descriptor(config,source,cache_directory,phase,output):
 cfg,physical,binaries,_=configuration(config);assert phase in binaries
 source=Path(source).resolve();output=Path(output).resolve();assert not output.exists()
 manifest=read(source/'manifest.json');cmd=list(manifest['command']);arguments=cmd[3:]
 if '--route' in arguments:arguments.remove('--route')
 assert '--analysis' in arguments
 for flag,value in [('--timing_report_npaths','10'),('--verify_route_file_switch_id','on')]:
  if flag in arguments:arguments[arguments.index(flag)+1]=value
  else:arguments += [flag,value]
 paths=dict(physical,binary=binaries[phase],packed=source/'packed.net',placement=source/'placed.place',route=source/'routed.route')
 assert sha(cmd[1])==sha(physical['architecture']) and sha(cmd[2])==sha(physical['circuit'])
 assert sha(cmd[cmd.index('--read_rr_graph')+1])==sha(physical['graph'])
 for key,name in [('packed','packed.net'),('placement','placed.place')]:assert sha(physical[key])==sha(source/name)
 mapping={'--read_rr_graph':'graph','--net_file':'packed','--place_file':'placement','--route_file':'route'}
 if 'sdc' in physical:mapping['--sdc_file']='sdc'
 assert ('sdc' in physical)==('--sdc_file' in arguments)
 for flag,key in mapping.items():arguments[arguments.index(flag)+1]='{'+key+'}'
 cache_directory=Path(cache_directory).resolve();assert sha(cache_directory/'completion.json')==cfg['full_graph_cache_completion_sha256']
 write(output,dict(format='standalone_native_observation_input_v1',files={k:dict(path=str(p),sha256=sha(p)) for k,p in paths.items()},analysis_arguments=arguments,full_graph_cache=dict(path=str(cache_directory),completion_sha256=sha(cache_directory/'completion.json')),phase=phase,runtime_config=str(Path(config).resolve()),runtime_config_sha256=sha(config)))
 return output

def admit_worker(descriptor,source,output):
 resource.setrlimit(resource.RLIMIT_AS,(64*1024**3,64*1024**3));package_files()
 config,paths,cache,command=inputs(descriptor,output);source=Path(source).resolve();m=read(source/'manifest.json')
 assert m['status']=='completed' and m['metrics']['native_full_check_passed'] and read(source/'independent_audit.json')['audit']['passed']
 assert paths['route']==source/'routed.route'
 for key,name in [('route','routed.route'),('packed','packed.net'),('placement','placed.place')]:
  assert sha(paths[key])==sha(source/name)==m['outputs'][name]['sha256']
 assert paths['graph']==Path(m['command'][m['command'].index('--read_rr_graph')+1]).resolve()
 for key,p in [('architecture',m['command'][1]),('circuit',m['command'][2])]:assert sha(paths[key])==sha(p)
 for name in list(os.environ):
  if name.startswith('VPR_'):del os.environ[name]
 return config,paths,cache,command
