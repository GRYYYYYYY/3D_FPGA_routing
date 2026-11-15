"""Seal exact completed worker observations without sealing an interrupted pool."""
from pathlib import Path
from retained_prefix_workflow import read, write, sha
from sealed_native_pool_replay import SealedNativePoolReplay


class CompletedNativeWorkerReplay:
    def __init__(self, original_pool, worker, directory):
        self.directory = Path(directory).resolve()
        self.directory.mkdir(exist_ok=False)
        original = Path(original_pool).resolve() / 'registration.json'
        r = read(original)
        self.worker = worker
        self.origin = Path(worker['job']) / 'completion.json'
        assert worker == read(self.origin) and worker['passed']
        assert worker['candidate_full_STA_passed'] and worker['native_transaction_succeeded']
        assert worker['static_identity'] == r['identity']
        assert worker['native_seed_order'] == r['native_seed_order']
        self.identity = r['identity']
        self.command = r['command']
        self.inputs = r['static_input_sha256']
        self.input_stats = r['static_input_stat_identity']
        self.environment_digest = r['execution_environment_digest']
        self.bound = dict(worker['artifact_sha256'])
        self.bound.update({str(original): sha(original), str(self.origin): sha(self.origin)})
        self.bound.update(self.inputs)
        self.registration = self.directory / 'registration.json'
        write(self.registration, dict(r, original_pool_registration=str(original),
              original_pool_final_seal_required=False, original_pool_seal_fabricated=False,
              source_sha256=dict(self.bound, **{str(Path(__file__).resolve()): sha(__file__)}),
              qualification='Read-only replay of ONE explicitly completed, hashed native worker. Identity and native environment belong to that original execution; no new process or analysis. This is a new observation-consumption seal, never the original interrupted pool final seal.'))
        self.bound[str(self.registration)] = sha(self.registration)
        self._require_static()
        assert all(sha(p) == h for p, h in self.bound.items())

    def _require_static(self):
        assert all(SealedNativePoolReplay._stat(p) == s for p, s in self.input_stats.items())
        assert sha(self.registration) == self.bound[str(self.registration)]
        assert sha(self.origin) == self.bound[str(self.origin)]

    def analyze(self, *args, **kwargs):
        raise RuntimeError('Completed worker replay cannot execute native analysis')

    def close(self):
        self._require_static()
        assert all(sha(p) == h for p, h in self.bound.items())
        write(self.directory / 'completion.json', dict(passed=True, native_calls=0,
              original_pool_seal_fabricated=False, completed_worker=str(self.origin),
              source_sha256=self.bound,
              qualification='Only this completed worker and its consumed static inputs were checked; no claim that other historical pool jobs passed or the interrupted workflow closed.'))
