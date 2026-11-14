#!/usr/bin/env python3
"""Extend the immutable analysis owner with per-job native transaction inputs."""
from pathlib import Path
from retained_prefix_workflow import D
s=(D/'native_analysis_pool_v2.py').read_text();s=s.replace('import json','import json\nimport math',1);s=s.replace('def analyze(self, route, *, echo=True, reuse=True):','def analyze(self, route, *, echo=True, reuse=True, native_request=None, objective="weighted_soft", crossing_domain=None, pressure_start=1.):')
s=s.replace('''        fingerprint=hashlib.sha256(json.dumps([self.identity,digest,bool(echo)]).encode()).hexdigest()''','''        repair = native_request is not None
        assert crossing_domain is None or repair
        assert objective in ["weighted_soft", "weighted_capacity", "physical_soft", "physical_capacity"]
        assert math.isfinite(pressure_start) and 0. < pressure_start <= 1000.
        originals = {"native_request.txt": Path(native_request).resolve()} if repair else {}
        if crossing_domain is not None: originals["crossing_domain.txt"] = Path(crossing_domain).resolve()
        input_hashes = {name: sha(path) for name,path in originals.items()}
        options = dict(operation="repair" if repair else "analysis", inputs=input_hashes,
                       objective=objective if repair else None,
                       pressure_start=pressure_start if repair else None)
        fingerprint=hashlib.sha256(json.dumps([self.identity,digest,bool(echo),options],sort_keys=True).encode()).hexdigest()''')
s=s.replace("            origin=self.cache[fingerprint];record=", "            origin=self.cache[fingerprint];assert all(sha(p)==h for p,h in origin['artifact_sha256'].items()),'Exact native cache artifact changed';record=")
needle="        while True:\n            self._ensure_epoch();inbox=Path(self.epoch['root'])/'inbox';index=self.epoch['jobs'];request=inbox/f'{index}.request';assert not request.exists()"
replacement="""        snapshots = {}
        for name,path in originals.items():
            target=job/name;shutil.copy2(path,target);assert sha(target)==input_hashes[name];snapshots[name]=target
        suffix=''
        if repair:
            domain=str(snapshots['crossing_domain.txt']) if 'crossing_domain.txt' in snapshots else ''
            suffix=' '+quoted('repair')+' '+quoted(snapshots['native_request.txt'])+' '+quoted(objective)+' '+quoted(domain)+' '+format(pressure_start,'.17g')
        while True:
            self._ensure_epoch();inbox=Path(self.epoch['root'])/'inbox';index=self.epoch['jobs'];request=inbox/f'{index}.request';assert not request.exists()"""
assert needle in s;s=s.replace(needle,replacement)
s=s.replace("quoted(native)+' '+str(int(bool(echo)))+'\\n'", "quoted(native)+' '+str(int(bool(echo)))+suffix+'\\n'")
s=s.replace("native_directory=str(native),static_identity=self.identity))", "native_directory=str(native),static_identity=self.identity,native_options=options,original_request_paths={name:str(path) for name,path in originals.items()},request_snapshot_sha256={str(snapshots[name]):h for name,h in input_hashes.items()}))")
s=s.replace("        assert sha(candidate)==digest and sha(route)==digest,'Candidate changed during native analysis'", """        transaction_succeeded=None
        if repair:
            transaction=native/'joint_native.log'
            lines=transaction.read_text().splitlines() if transaction.exists() else []
            final=lines[-1].split() if lines else []
            complete=complete and bool(final) and final[0]=='COMPLETE' and final[-1]=='occupancy_restored'
            if complete:transaction_succeeded=bool(int(final[1]))
            for name in ['joint_native.log','vertical_domain.log']:
                if (native/name).exists():paths.append(native/name)
        paths += list(snapshots.values())
        assert all(sha(path)==input_hashes[name] and sha(snapshots[name])==input_hashes[name] for name,path in originals.items()),'Native request changed during job'
        assert sha(candidate)==digest and sha(route)==digest,'Candidate changed during native analysis'""")
s=s.replace("passed=bool(complete),reused=False,route_sha256", "passed=bool(complete),native_transaction_succeeded=transaction_succeeded,native_options=options,reused=False,route_sha256")
s=s.replace("qualification='Child time includes fork/native LOAD/FULL/pin synchronization/STA.", "qualification='Worker FULLSTA describes the input state; private native candidate trees still require independent replacement/FULLSTA and acceptance. Failed search transaction is distinct from worker failure. Child time includes fork/native LOAD/FULL/pin synchronization/STA.")
(D/'native_repair_analysis_pool.py').write_text(s)
