"""Run the packaged guard/process checks, recording actual receipts in a new directory."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from runtime_common import sha256,write_json

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    package=Path(__file__).resolve().parent;manifest=json.loads((package/'artifact_manifest.json').read_text())
    for name,digest in manifest['sha256'].items():assert sha256(package/name)==digest,name
    output=a.output.resolve();output.mkdir(parents=True,exist_ok=False)
    env={k:v for k,v in os.environ.items() if k not in ['PYTHONPATH','PYTHONHOME','LD_PRELOAD','LD_AUDIT','LD_LIBRARY_PATH']}
    env['PYTHONDONTWRITEBYTECODE']='1'
    commands=[('guard',[sys.executable,str(package/'test_seccomp_thread_guard.py')])]
    commands += [(mode,[sys.executable,str(package/'test_runtime_io.py'),'--output',str(output/mode),'--mode',mode])
                 for mode in ['normal','timeout','thread','mutated','wrong_binary']]
    results=[]
    for name,command in commands:
        r=subprocess.run(command,capture_output=True,text=True,env=env,cwd=package,timeout=30)
        receipt=dict(case=name,command=command,returncode=r.returncode,stdout=r.stdout,stderr=r.stderr)
        write_json(output/(name+'_execution.json'),receipt);assert r.returncode==0,receipt
        results.append(dict(case=name,passed=True))
    for name,digest in manifest['sha256'].items():assert sha256(package/name)==digest,name
    write_json(output/'completion.json',dict(passed=True,artifact_manifest_sha256=sha256(package/'artifact_manifest.json'),
        cases=results,VPR_calls_new=0,qualification='Runtime component self-test, not FPGA quality or whole-method confirmation.'))
    print(json.dumps(dict(passed=True,cases=len(results),VPR_calls_new=0)))

if __name__=='__main__':main()
