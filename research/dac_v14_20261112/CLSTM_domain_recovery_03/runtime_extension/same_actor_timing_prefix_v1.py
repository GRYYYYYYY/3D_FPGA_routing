"""Reuse the original first timing portfolio, without replaying its queries."""
from pathlib import Path
from retained_prefix_workflow import read,write,sha
from recovery_prefix_v1 import Evidence,live_identity

def timing_envelope_gate(plan,old,initial,anchor,limits,args):
    assert plan['recovery_mode']=='timing_only_after_closed_resource'
    assert Path(old['initial_state']).resolve()==Path(initial).resolve()
    for key in ['policy','budget_mode','fraction','native_mode']:
        assert old[key]==getattr(args,key),key
    assert old['objective']=='weighted_soft' and old['anchor']==anchor
    assert old['fixed_absolute_limits']==limits
    assert not (args.resume_from or args.reuse_plan or args.reuse_native_batch or args.reuse_query_batch or args.reuse_exchange)
    assert [Path(p).resolve() for p in args.reuse_portfolio]==[Path(plan['original_timing_portfolio']).resolve()]

class TimingPrefix:
    def __init__(self,plan_path,initial,anchor,limits,args):
        self.plan_path=Path(plan_path).resolve();self.plan=read(self.plan_path)
        self.evidence=Evidence();self.evidence.bind(self.plan_path)
        old=Path(self.plan['original_actor']);reg=read(old/'registration.json')
        assert not live_identity(reg['pid'],reg['start_ticks'])
        timing_envelope_gate(self.plan,reg,initial,anchor,limits,args)
        self.evidence.verify(self.plan['prefix_sha256']);self.evidence.verify(reg['source_sha256'])
        # This adapter targets the actual CLSTM cut point before the first
        # proposal finished. A later prefix needs explicit accepted/attempted
        # history support rather than silently resetting it.
        for name in ['steps.json','attempts.json']:
            if (old/name).exists():
                self.evidence.bind(old/name);assert read(old/name)==[],name
        assert not (old/'resume_state.json').exists(),'Later timing checkpoint needs separate continuation'
        menu=Path(self.plan['original_timing_portfolio']);v=read(menu)
        assert v['passed'] and Path(v['source_state']).resolve()==Path(initial).resolve()
        assert read(v['base_plan'])['selection']['fraction']==args.fraction
        pending=[menu];seen=set()
        while pending:
            path=Path(pending.pop()).resolve()
            if path in seen:continue
            seen.add(path);self.evidence.bind(path)
            if path.suffix!='.json' or path.stat().st_size>4*1024**2:continue
            record=read(path)
            if not isinstance(record,dict):continue
            for source,digest in record.get('source_sha256',{}).items():
                self.evidence.bind(source,digest)
                if Path(source).suffix=='.json':pending.append(Path(source))
        self.menu=menu

    def finish(self,batch):
        self.evidence.unchanged();done=read(batch/'completion.json')
        done.update(cost_scope='new_recovery_suffix_only',fresh_complete_algorithm_seconds=None,
            recovered_same_actor_timing_portfolio=str(self.menu),prior_native_queries_repeated=False,
            qualification='Continued the original first timing portfolio from its unchanged original handoff/root/limits. Completed feedback/query/portfolio creation and completed native stages are reused; only missing work is new. Development recovery suffix, not cold cost, independent input or frozen confirmation.')
        write(batch/'completion.json',done)
        write(batch/'timing_prefix_consumption_seal.json',dict(passed=True,source_sha256=self.evidence.bound,
            original_receipts_changed=False,query_creation_cost_borrowed=False,new_native_calls_from_prefix=0))
