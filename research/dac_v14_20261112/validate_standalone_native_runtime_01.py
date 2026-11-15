"""Execute relocated runtime/guard probes and verify scientific parser/audit code identity."""
import ast,json,os,shutil,subprocess,tempfile
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
package=D/'standalone_native_runtime_dev_01';report=D/'standalone_native_runtime_validation_01';report.mkdir(exist_ok=False)
origin=D.parents[1];provenance=read(package/'provenance.json');function_checks=[]
def nodes(p):return {x.name:ast.dump(x,include_attributes=False) for x in ast.parse(p.read_text()).body if isinstance(x,ast.FunctionDef)}
for name,row in provenance['source_files'].items():
 if row.get('transformation')=='byte_exact':assert sha(package/name)==row['origin_sha256']
 if row.get('extracted_functions'):
  old,new=nodes(Path(row['origin'])),nodes(package/name)
  for f in row['extracted_functions']:assert old[f]==new[f];function_checks.append(dict(file=name,function=f,AST_exact=True))
for f in package.glob('*.py'):compile(f.read_text(),str(f),'exec')
relocated=Path(tempfile.mkdtemp(prefix='standalone-routing-runtime-'));shutil.copytree(package,relocated/'runtime');target=relocated/'runtime'
env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH']};env['PYTHONDONTWRITEBYTECODE']='1'
command=['/usr/bin/python3',str(target/'test_seccomp_thread_guard.py')]
r=subprocess.run(command,capture_output=True,text=True,env=env,cwd=target,timeout=30);assert r.returncode==0,(r.stdout,r.stderr)
write(report/'guard_test.json',dict(passed=True,command=command,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
results=[]
for mode in ['normal','timeout','thread','mutated','wrong_binary']:
 output=relocated/mode;command=['/usr/bin/python3',str(target/'test_runtime_io.py'),'--output',str(output),'--mode',mode,'--forbid-prefix',str(origin)]
 r=subprocess.run(command,capture_output=True,text=True,cwd=target,env=env,timeout=20)
 write(report/(mode+'_execution.json'),dict(command=command,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr))
 assert r.returncode==0,(mode,r.stdout,r.stderr)
 result=read(output/'test.json');assert result['passed'];results.append(result)
 shutil.copytree(output,report/mode)
# Exactly copied parser against real previously measured native logs is read-only.
log=origin/'research/dac_v14_20261112/complete_serial_transfer_dev_01/spmv_native/flow/initial/runs/state/stdout.log'
namespace={};exec(compile((package/'runtime_metrics.py').read_text(),str(package/'runtime_metrics.py'),'exec'),namespace)
actual=namespace['parse_metrics'](log.read_text());expected=read(log.parent/'manifest.json')['metrics'];assert actual==expected
write(report/'completion.json',dict(passed=True,relocated_directory=str(relocated),historical_project_reads_forbidden_in_runtime_tests=True,guard_selftests_passed=True,process_tests=results,extracted_function_identity=function_checks,real_native_log_parser_exact=True,original_log=str(log),VPR_calls_new=0,full_method_packaged=False,source_sha256={str(f):sha(f) for f in [Path(__file__).resolve(),log,log.parent/'manifest.json',*package.iterdir()] if f.is_file()},qualification='Native I/O component runs after copying outside the repository with historical project reads forbidden. Byte-identical seccomp guard and AST-identical scientific parser/physical-audit functions retained. Actual current executable libraries, serial guard, timeout, frozen-input mutation and wrong-executable rejection tested. No VPR solver run and no new independent scientific sample; remaining full method prerequisites are not yet removed.'))
print(dict(passed=True,process_cases=len(results),exact_functions=len(function_checks),VPR_calls_new=0,relocated_directory=str(relocated)),flush=True)
