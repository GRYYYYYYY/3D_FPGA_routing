#!/usr/bin/env python3
"""Build the pinned LaZagna VTR9 port; disclose optional build-only repairs."""
import argparse
import json
import shutil
import subprocess

from lazagna_vtr9_common import BASE, ROOT, SOURCE, LAZAGNA, COMMIT, run, sha256, utc, write_json


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--serial', action='store_true', help='Use existing serial execution-engine options')
    parser.add_argument('--portability', action='store_true', help='Separate copy with portable includes and CMake linkage repair')
    args = parser.parse_args()
    suffix = ('_buildfix' if args.portability else '') + ('_serial' if args.serial else '')
    destination = ROOT / ('artifacts/bin/lazagna-vtr9-port' + ('-buildfix' if args.portability else ''))
    if destination.exists():
        raise RuntimeError('Archive destination already exists')
    assert git(SOURCE, 'rev-parse', '--show-toplevel') == str(SOURCE)
    assert git(SOURCE, 'rev-parse', 'HEAD') == COMMIT
    assert not git(SOURCE, 'status', '--porcelain')
    expected = {'lazagna': (LAZAGNA, '44acf9d27ed01d4a7496773aa8663266c9b5a73b'),
                'openfpga': (LAZAGNA / 'OpenFPGA', '9f473f97921cd9e870c6ea9c418bd3d4cb6f4360'),
                'vtr': (SOURCE, COMMIT)}
    sources = {}
    for name, (path, commit) in expected.items():
        assert git(path, 'rev-parse', 'HEAD') == commit
        sources[name] = dict(path=str(path), commit=commit, status=git(path, 'status', '--porcelain'))
    frozen = json.loads((ROOT / 'docs/handoff_source_evidence_2026-10-25.json').read_text())['frozen_evidence_sha256']
    assert all(sha256(ROOT / p) == h for p, h in frozen.items())
    lock = dict(utc=utc(), sources=sources,
        vtr_submodules=git(SOURCE, 'submodule', 'status'), protected_files=frozen,
        source_setup=['git clone --shared --no-checkout vendor/LaZagna-paper/OpenFPGA/vtr-verilog-to-routing vendor/lazagna-vtr9-src',
                      f'git -C vendor/lazagna-vtr9-src checkout --detach {COMMIT}',
                      'git -C vendor/lazagna-vtr9-src submodule update --init libs/EXTERNAL/libcatch2'],
        scope='Standalone VPR from the exact nested commit. OpenFPGA executable, synthesis and bitstream flow are not built by this script.')
    if not (BASE / 'source_lock.json').exists():
        write_json(BASE / 'source_lock.json', lock)
    else:
        assert json.loads((BASE / 'source_lock.json').read_text())['sources'] == sources
    source = SOURCE
    patch = None
    if args.portability:
        source = ROOT / 'vendor/lazagna-vtr9-buildfix-src'
        if source.exists():
            raise RuntimeError('Buildfix checkout already exists')
        subprocess.run(['git', 'clone', '--shared', str(SOURCE), str(source)], check=True)
        subprocess.run(['git', '-C', str(source), '-c', 'protocol.file.allow=always',
                        '-c', f'submodule.libs/EXTERNAL/libcatch2.url={SOURCE}/libs/EXTERNAL/libcatch2',
                        'submodule', 'update', '--init', 'libs/EXTERNAL/libcatch2'], check=True)
        header = source / 'libs/EXTERNAL/libtatum/libtatum/tatum/TimingReporter.hpp'
        old = header.read_text()
        prefix = '/home/OpenFPGA_LaZagna_merge/OpenFPGA_testing/OpenFPGA/vtr-verilog-to-routing/vpr/src/'
        assert old.count(prefix) == 2
        header.write_text(old.replace(prefix + 'base/vpr_context.h', 'vpr_context.h')
                          .replace(prefix + 'pack/prepack.h', 'prepack.h'))
        cmake_file = source / 'libs/EXTERNAL/libtatum/CMakeLists.txt'
        old = cmake_file.read_text()
        assert old.count('target_link_libraries(libtatum PRIVATE vpr_interface)') == 1
        cmake_file.write_text(old.replace('target_link_libraries(libtatum PRIVATE vpr_interface)',
                                         'target_link_libraries(libtatum vpr_interface)'))
        patch = ROOT / 'patches/lazagna-vtr9-build-portability.patch'
        patch.write_text(subprocess.check_output(['git', '-C', str(source), 'diff'], text=True))
        write_json(BASE / 'buildfix_protocol.json', dict(utc=utc(), original_commit=COMMIT,
            source=str(source), patch=str(patch), patch_sha256=sha256(patch),
            changes=['Replace two developer-machine absolute header paths with existing include-path names.',
                     'Use consistent plain target_link_libraries signature for the existing vpr_interface dependency.'],
            unchanged='No placement, routing, graph generation or timing arithmetic is modified.',
            original_failures=['runs/configure_vpr/manifest.json', 'runs/build_vpr_serial/manifest.json']))
    build = ROOT / ('build/lazagna-vtr9-port' + suffix)
    command = ['cmake', '-S', source, '-B', build, '-G', 'Ninja',
               '-DVPR_USE_EZGL=off', '-DVPR_USE_SERVER=OFF', '-DVTR_IPO_BUILD=off',
               '-DVTR_ENABLE_CAPNPROTO=OFF', '-DVPR_ENABLE_INTERCHANGE=OFF',
               '-DWITH_ABC=OFF', '-DWITH_PARMYS=OFF', '-DWITH_ODIN=OFF',
               '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON']
    if args.serial:
        command += ['-DTATUM_EXECUTION_ENGINE=serial', '-DVPR_EXECUTION_ENGINE=serial']
    r = run('configure_vpr' + suffix, command, inputs=[source / 'CMakeLists.txt', *([patch] if patch else [])], timeout=600)
    if r['status'] != 'completed':
        raise RuntimeError('Configure failed; original receipt retained')
    r = run('build_vpr' + suffix, ['cmake', '--build', build, '--target', 'vpr', '-j', 24],
            inputs=[build / 'CMakeCache.txt'], timeout=3600)
    if r['status'] != 'completed':
        raise RuntimeError('Build failed; original receipt retained')
    destination.mkdir(parents=True)
    shutil.copy2(build / 'vpr/vpr', destination / 'vpr')
    shutil.copy2(build / 'CMakeCache.txt', destination / 'CMakeCache.txt')
    r = run('vpr_version', [destination / 'vpr', '--version'], inputs=[destination / 'vpr'], timeout=30)
    assert r['status'] == 'completed'
    assert not git(SOURCE, 'status', '--porcelain')
    write_json(destination / 'manifest.json', dict(utc=utc(), sources=sources,
        binary_sha256=sha256(destination / 'vpr'), cache_sha256=sha256(destination / 'CMakeCache.txt'),
        version_output=(BASE / 'runs/vpr_version/stdout.log').read_text(),
        submodules=git(SOURCE, 'submodule', 'status'), configure_command=list(map(str, command)),
        compiler=subprocess.check_output(['c++', '--version'], text=True).splitlines()[0],
        cmake=subprocess.check_output(['cmake', '--version'], text=True).splitlines()[0],
        build_receipt=str(BASE / ('runs/build_vpr' + suffix) / 'manifest.json'),
        build_source=str(source), build_source_status=git(source, 'status', '--porcelain'),
        source_patch=str(patch) if patch else None, patch_sha256=sha256(patch) if patch else None,
        scope='Standalone VPR target with explicitly recorded build repairs, if any; not a full OpenFPGA or bitstream reproduction.'))


if __name__ == '__main__':
    main()
