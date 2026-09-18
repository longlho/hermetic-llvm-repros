#!/usr/bin/env python3
"""Run isolated public-source repros; raw logs stay in ignored results/."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
CASES = {
    'bindgen-resource-headers': {'bindgen': ['build', '//:probe'], 'bindgen-linux': ['build', '//:probe', '--platforms=@llvm//platforms:linux_x86_64']},
    'macos-go-link': {
        'plain': ['build', '//:plain'],
        'exec-transition': ['build', '//:exec_transition'],
        'transitioned': ['build', '//:transitioned'],
        'public-headers': ['build', '//:public_headers'],
        'internal-headers': ['build', '//:internal_headers'],
    },
    'msvc-integration': {
        'limits': ['build', '//:limits'],
        'legacy-stdio': ['build', '//:legacy_stdio'],
        'stdio-mode': ['build', '//:stdio_mode'],
        'crt-local': ['build', '//:crt_static_local'],
        'crt-static': ['build', '//:crt_static_local', '--@llvm//toolchain/features/msvc:crt_mode=static'],
        'overlay': ['build', '@llvm//tools/case_insensitive_vfs:case_insensitive_vfs', '@llvm//tools:clang'],
    },
    'windows-bootstrap': {
        'hello': ['build', '//:hello'],
        'generator': ['build', '@llvm//tools/case_insensitive_vfs:case_insensitive_vfs'],
    },
    'llvm-nm-target': {
        'public': ['build', '//:public_tool'],
        'custom': ['build', '//:custom_alias'],
    },
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', choices=CASES)
    parser.add_argument('--case', required=True)
    parser.add_argument('--variant', choices=['upstream', 'patched'], default='upstream')
    parser.add_argument('--bazel', default='bazel')
    parser.add_argument('--host-sdk', action='store_true', help='Use installed Xcode SDK on macOS instead of public Apple archive')
    parser.add_argument('--accept-msvc-eula', action='store_true', help='Accept Microsoft runtime and Windows SDK licenses for this run')
    parser.add_argument('--analyze-only', action='store_true')
    args = parser.parse_args()
    if args.case not in CASES[args.folder]:
        parser.error('Cases: ' + ', '.join(CASES[args.folder]))
    windows = args.folder in ('msvc-integration', 'windows-bootstrap') and args.case != 'overlay'
    if windows and not args.accept_msvc_eula:
        parser.error('Windows cases require --accept-msvc-eula after reviewing the Microsoft licenses')
    if args.folder == 'windows-bootstrap' and sys.platform != 'win32':
        parser.error('Native bootstrap repro must run on Windows; cross-compilation is a different control')
    work = ROOT / '.work' / args.folder / args.variant
    work.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / args.folder, work, dirs_exist_ok=True, ignore=shutil.ignore_patterns('README.md', '*.patch', 'MODULE.bazel.lock', 'bazel-*'))
    if args.variant == 'patched':
        patches = sorted((ROOT / args.folder).glob('*.patch'))
        if not patches:
            parser.error('No justified candidate patch for this folder; see README.md')
        for patch in patches:
            shutil.copy2(patch, work / patch.name)
        with (work / 'MODULE.bazel').open('a') as module:
            module.write('\nsingle_version_override(module_name = "llvm", patch_strip = 1, patches = ' + repr([p.name for p in patches]) + ')\n')
    command = [args.bazel, '--batch', '--nosystem_rc', '--nohome_rc'] + CASES[args.folder][args.case]
    command += ['--color=no', '--curses=no']
    if windows:
        command += ['--platforms=@llvm//platforms:windows_x86_64_msvc', '--repo_env=BAZEL_MSVC_RUNTIME_VISUAL_STUDIO_EULA=1', '--repo_env=BAZEL_WINDOWS_SDK_EULA=1']
    if args.host_sdk:
        command += ['--repo_env=BAZEL_MACOS_USE_HOST_SDK=1']
    if args.analyze_only:
        command += ['--nobuild']
    result_dir = ROOT / 'results' / args.folder / args.variant
    result_dir.mkdir(parents=True, exist_ok=True)
    logfile = result_dir / (args.case + '.log')
    with logfile.open('w') as log:
        result = subprocess.run(command, cwd=work, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode == 0 and args.case == 'overlay':
        tool_paths = []
        for label in ['@llvm//tools/case_insensitive_vfs:case_insensitive_vfs', '@llvm//tools:clang']:
            query = subprocess.check_output([args.bazel, '--batch', '--nosystem_rc', '--nohome_rc', 'cquery', label, '--output=files'] + (['--repo_env=BAZEL_MACOS_USE_HOST_SDK=1'] if args.host_sdk else []), cwd=work, text=True)
            relative = query.strip().splitlines()[-1]
            if relative.startswith('external/'):
                path = work / 'bazel-out/../../../' / relative
                execroot = subprocess.check_output([args.bazel, '--batch', '--nosystem_rc', '--nohome_rc', 'info', 'execution_root'], cwd=work, text=True).strip()
                path = Path(execroot) / relative
            else:
                path = work / relative
            tool_paths.append(str(path.resolve()))
        with logfile.open('a') as log:
            result = subprocess.run([sys.executable, str(ROOT / 'msvc-integration/overlay_probe.py')] + tool_paths, cwd=work, stdout=log, stderr=subprocess.STDOUT)
    print(f'{args.folder}/{args.case} [{args.variant}]: exit {result.returncode}')
    print(f'Local log: {logfile.relative_to(ROOT)} (ignored by git; review before sharing)')
    return result.returncode

if __name__ == '__main__':
    raise SystemExit(main())
