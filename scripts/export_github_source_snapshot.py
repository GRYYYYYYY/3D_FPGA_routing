#!/usr/bin/env python3
"""Export source changes without touching live checkouts; verify patch round trips."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    'native': ('vendor/vtr', 'https://github.com/verilog-to-routing/vtr-verilog-to-routing.git'),
    'architecture_r1': ('vendor/vtr-architecture-src', 'https://github.com/verilog-to-routing/vtr-verilog-to-routing.git'),
    'lazagna_b2': ('vendor/lazagna-vtr9-buildfix-src', 'https://github.com/IY2002/vtr-verilog-to-routing.git'),
    'placement_p1': ('vendor/beyond-flatland-src', 'https://github.com/IY2002/Beyond-Flatland.git'),
    'partition': ('results/architecture_flow_20261027/single_thread_candidate_20261103/openroad_git', 'https://github.com/The-OpenROAD-Project/OpenROAD.git'),
}


def git(cwd, *args):
    return subprocess.check_output(['git', *args], cwd=cwd)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def export(destination):
    destination.mkdir(parents=True, exist_ok=False)
    manifest = {'utc': datetime.now(timezone.utc).isoformat(), 'sources': {},
                'scope': 'Source snapshot, not a completed experimental archive. No builds or solvers executed.'}
    for label, (relative, url) in SOURCES.items():
        source = ROOT / relative
        commit = git(source, 'rev-parse', 'HEAD').decode().strip()
        changed = git(source, 'diff', 'HEAD', '--name-only', '-z').decode().strip('\0').split('\0')
        changed = [name for name in changed if name]
        untracked = git(source, 'ls-files', '--others', '--exclude-standard', '-z').decode().strip('\0').split('\0')
        added = [name for name in untracked if name and not name.startswith('build-local/')]
        before = {name: digest((source / name).read_bytes()) for name in changed + added}
        patch = git(source, 'diff', 'HEAD', '--binary', '--no-ext-diff')
        for name in added:
            result = subprocess.run(['git', 'diff', '--no-index', '--binary', '--', '/dev/null', name],
                                    cwd=source, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode != 1:
                raise RuntimeError(result.stderr.decode())
            patch += result.stdout
        patch_file = destination / (label + '.patch')
        patch_file.write_bytes(patch)
        with tempfile.TemporaryDirectory(prefix='routing-source-verify-') as temporary:
            target = Path(temporary)
            subprocess.run(['git', 'init', '-q', str(target)], check=True)
            for name in changed:
                output = target / name
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(git(source, 'show', f'{commit}:{name}'))
            subprocess.run(['git', 'apply', '--check', str(patch_file.resolve())], cwd=target, check=True)
            subprocess.run(['git', 'apply', str(patch_file.resolve())], cwd=target, check=True)
            for name, expected in before.items():
                assert digest((target / name).read_bytes()) == expected, (label, name)
                assert digest((source / name).read_bytes()) == expected, ('live source changed', label, name)
        manifest['sources'][label] = {
            'local_source': relative, 'upstream_url': url, 'commit': commit,
            'patch': str(patch_file.relative_to(ROOT)), 'patch_sha256': digest(patch),
            'files_sha256': before, 'patch_roundtrip_verified': True,
            'excluded_untracked': [name for name in untracked if name and name not in added],
        }
        print(label, len(before), 'source files verified')
    (destination / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', type=Path, help='New directory under the project root')
    args = parser.parse_args()
    export(args.destination.resolve())
