from pathlib import Path
from retained_prefix_workflow import read
def run_dir(state):return Path(read(state/'completion.json')['run'])
