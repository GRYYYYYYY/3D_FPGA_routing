"""Read-only exact consumption of a fully sealed native pool; never resubmit jobs."""
from pathlib import Path
from retained_prefix_workflow import read, sha


class SealedNativePoolReplay:
    """Expose immutable pool identities for materialization with zero native calls."""
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.registration = self.directory / 'registration.json'
        self.completion = self.directory / 'completion.json'
        self.registration_sha256 = sha(self.registration)
        self.completion_sha256 = sha(self.completion)
        r = read(self.registration)
        c = read(self.completion)
        assert c['passed'] and c['static_inputs_unchanged'] and c['artifacts_unchanged']
        assert all(sha(p) == h for p, h in c['source_sha256'].items())
        self.identity = r['identity']
        self.command = r['command']
        self.inputs = r['static_input_sha256']
        self.input_stats = r['static_input_stat_identity']
        self.binary_sha256 = sha(self.command[0])
        self.environment_digest = r['execution_environment_digest']
        self.jobs = read(self.directory / 'jobs.json')
        self._require_static()
        assert all(sha(p) == h for p, h in self.inputs.items())

    @staticmethod
    def _stat(path):
        s = Path(path).stat()
        return [s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns]

    def _require_static(self):
        """Fail on changed binary/static/runtime identities; no fallback execution."""
        assert sha(self.registration) == self.registration_sha256
        assert sha(self.completion) == self.completion_sha256
        assert all(self._stat(p) == s for p, s in self.input_stats.items())

    def analyze(self, *args, **kwargs):
        """Prevent replay consumers from manufacturing or silently redoing evidence."""
        raise RuntimeError('Sealed pool replay cannot analyze; provide an explicitly completed native observation')

    def close(self):
        """Revalidate without changing old pool receipts, inputs or artifact bytes."""
        self._require_static()
        assert all(sha(p) == h for p, h in self.inputs.items())
        assert all(sha(p) == h for j in self.jobs for p, h in j['artifact_sha256'].items())
