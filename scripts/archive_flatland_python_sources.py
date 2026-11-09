#!/usr/bin/env python3
"""Archive current statically resolved local sources without importing runners."""
import argparse
import ast
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys

from lazagna_common import ROOT, sha256, utc, write_json

BASE = ROOT / 'results/architecture_flow_20261027'
SCRIPTS = ROOT / 'scripts'


def identity(path):
    stat = path.stat()
    return [stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns]


def discover(seeds):
    pending = list(seeds)
    sources = {}
    imports = {}
    unresolved = set()
    dynamic = []
    while pending:
        path = Path(pending.pop()).resolve()
        if path in sources:
            continue
        assert path.is_relative_to(ROOT) and path.suffix == '.py'
        before = identity(path)
        data = path.read_bytes()
        assert identity(path) == before, f'Source changed while reading: {path}'
        sources[path] = (data, before)
        tree = ast.parse(data, filename=str(path))
        dependencies = set()
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module]
            for module in modules:
                root = path.parent if isinstance(node, ast.ImportFrom) and node.level else SCRIPTS
                candidate = root.joinpath(*module.split('.')).with_suffix('.py')
                if not candidate.is_file():
                    candidate = root.joinpath(*module.split('.'), '__init__.py')
                if candidate.is_file() and candidate.resolve().is_relative_to(ROOT):
                    dependencies.add(candidate.resolve())
                else:
                    unresolved.add(module)
            if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                    and node.value.endswith('.py') and len(node.value) < 4096
                    and not any(c in node.value for c in ('\n', '\r', '\0'))):
                value = Path(node.value)
                for candidate in (path.parent / value, ROOT / value, SCRIPTS / value):
                    if candidate.is_file() and candidate.resolve().is_relative_to(ROOT):
                        dependencies.add(candidate.resolve())
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, 'attr', '')
                if name in ('__import__', 'import_module'):
                    dynamic.append(dict(source=str(path.relative_to(ROOT)), line=node.lineno,
                                        expression=ast.unparse(node)))
        imports[str(path.relative_to(ROOT))] = sorted(str(p.relative_to(ROOT)) for p in dependencies)
        pending.extend(dependencies)
    return sources, imports, sorted(unresolved), dynamic


def main(output):
    output = Path(output)
    assert not output.exists()
    training_path = BASE / 'training_jobs.json'
    registration_path = BASE / 'registered_study_continuation_20261029/registration.json'
    training = json.loads(training_path.read_text())
    registration = json.loads(registration_path.read_text())
    bindings = dict(training['source_sha256'])
    for path, digest in registration['source_and_protocol_sha256'].items():
        assert path not in bindings or bindings[path] == digest
        bindings[path] = digest
    for path, digest in bindings.items():
        assert sha256(path) == digest, f'Existing binding changed: {path}'
    seeds = {Path(path) for path in bindings if Path(path).suffix == '.py'}
    seeds.add(Path(__file__).resolve())
    sources, imports, unresolved, dynamic = discover(seeds)
    assert not (BASE / 'selected_configs.json').exists(), 'Capture must precede selection and held-out evaluation'
    assert not (BASE / 'evaluation_jobs.json').exists()
    output.mkdir(parents=True, exist_ok=False)
    rows = {}
    for path, (data, before) in sorted(sources.items()):
        relative = path.relative_to(ROOT)
        snapshot = output / 'files' / relative
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        snapshot.write_bytes(data)
        digest = hashlib.sha256(data).hexdigest()
        assert sha256(snapshot) == sha256(path) == digest and identity(path) == before
        expected = bindings.get(str(path))
        if expected is not None:
            assert expected == digest
        rows[str(relative)] = dict(sha256=digest, snapshot=str(snapshot),
                                  captured_source_identity=before,
                                  matches_prior_registered_binding=expected is not None)
    versions = {}
    for distribution in ('lxml', 'numpy', 'matplotlib'):
        try:
            versions[distribution] = importlib.metadata.version(distribution)
        except importlib.metadata.PackageNotFoundError:
            versions[distribution] = None
    for path, digest in bindings.items():
        assert sha256(path) == digest, f'Existing binding changed during capture: {path}'
    write_json(output / 'manifest.json', dict(utc=utc(), status='current_local_sources_archived_before_heldout',
        source_sha256=sha256(__file__), files=rows, local_dependency_edges=imports,
        local_source_count=len(rows), prior_binding_matches=sum(r['matches_prior_registered_binding'] for r in rows.values()),
        verified_existing_bindings=bindings,
        anchors_sha256={str(p): sha256(p) for p in (training_path, registration_path,
            BASE / 'core_dump_execution_amendment_20261029.json')},
        python=dict(version=sys.version, implementation=platform.python_implementation()),
        selected_distribution_versions=versions, imports_without_local_source=unresolved,
        dynamic_import_calls=dynamic,
        limitations=['Static imports and literal local Python script paths only; dynamic runtime paths may require separate evidence.',
            'For sources lacking a prior registered binding, this is a current capture, not proof of their state at the start of training.',
            'Selected package versions do not replace the separate compiled-tool, model-input and environment provenance records.']))
    print(output / 'manifest.json', len(rows), 'sources;', sum(r['matches_prior_registered_binding'] for r in rows.values()), 'prior bindings matched')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=BASE / 'python_execution_sources_20261029')
    main(parser.parse_args().output)
