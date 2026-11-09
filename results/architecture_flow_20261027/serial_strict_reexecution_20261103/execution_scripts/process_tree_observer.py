"""Sample a child process tree without changing the observed process environment.

Sampling can miss short-lived processes or threads and is not proof of absence.
The observer runs in the supervisor and has overhead; do not call timing isolated.
"""
from pathlib import Path
import threading
import time


class ProcessTreeObserver:
    def __init__(self, pid, interval=0.01):
        self.pid = pid
        self.interval = interval
        self.stop_event = threading.Event()
        self.observations = {}
        self.samples = 0
        self.read_errors = 0
        self.worker = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self.worker.start()

    def stop(self):
        self.stop_event.set()
        self.worker.join()
        items = list(self.observations.values())
        return dict(method='proc_process_tree_polling', interval_seconds=self.interval,
                    samples=self.samples, read_errors=self.read_errors,
                    peak_threads=max((x['peak_threads'] for x in items), default=None),
                    violation_observed=any(x['peak_threads']>1 for x in items),
                    processes=items,
                    limitation='Polling can miss transient threads/processes and introduces supervisor overhead; absence is not proof.')

    def _run(self):
        while not self.stop_event.is_set():
            pending = [self.pid]; seen = set(); self.samples += 1
            while pending:
                pid = pending.pop()
                if pid in seen:
                    continue
                seen.add(pid)
                path = Path('/proc')/str(pid)
                try:
                    lines = (path/'status').read_text().splitlines()
                    fields = dict(x.split(':',1) for x in lines if ':' in x)
                    name = fields['Name'].strip(); threads = int(fields['Threads'].strip())
                    stat = (path/'stat').read_text(); start = stat[stat.rfind(')')+2:].split()[19]
                    key = f'{pid}:{start}'
                    row = self.observations.setdefault(key,dict(pid=pid,start_ticks=start,name=name,peak_threads=0,samples=0))
                    row['peak_threads'] = max(row['peak_threads'],threads);row['samples'] += 1
                    for task in (path/'task').iterdir():
                        try:pending.extend(int(v) for v in (task/'children').read_text().split())
                        except (OSError,ValueError):self.read_errors += 1
                except (OSError,KeyError,ValueError,IndexError):
                    self.read_errors += 1
            self.stop_event.wait(self.interval)
