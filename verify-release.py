"""Verify fixed bugs and exact negative controls against the selected release."""
import argparse
from dataclasses import dataclass
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

@dataclass(frozen=True)
class Case:
    folder: str
    name: str
    variant: str = 'upstream'
    failure: str | None = None
    llvm_version: str | None = None

GROUPS = {
    'resource-headers': [
        Case('merged-resource-headers', 'compile_only'),
        Case('merged-resource-headers', 'compile_and_link', failure="fatal error: 'stddef.h' file not found"),
        Case('merged-resource-headers', 'compile_and_link', llvm_version='0.8.25'),
    ],
    'bindgen': [Case('bindgen-resource-headers', name) for name in ('bindgen', 'bindgen-linux')],
    'go': [Case('macos-go-link', name) for name in ('plain', 'transitioned', 'exec-transition', 'public-headers')] + [Case('macos-go-link', 'internal-headers', failure='not visible')],
    'msvc': [
        Case('msvc-integration', 'limits', failure='_I64_MAX.*undeclared|undeclared.*_I64_MAX'),
        Case('msvc-integration', 'limits', 'patched'),
        Case('msvc-integration', 'legacy-stdio', failure='(could not|cannot|unable to).*legacy_stdio_definitions.lib'),
        Case('msvc-integration', 'legacy-stdio', 'patched'),
        Case('msvc-integration', 'stdio-mode', failure='ISO wide stdio|stdio.*mode|_CRT_STDIO_ISO_WIDE_SPECIFIERS'),
        Case('msvc-integration', 'stdio-mode', 'patched'),
        Case('msvc-integration', 'crt-local', failure='static CRT requested but dynamic CRT selected'),
        Case('msvc-integration', 'crt-local', 'patched', failure='dynamic_crt_configuration is provided by all of the following features: msvc_configured_dynamic_crt static_link_msvcrt'),
        Case('msvc-integration', 'crt-static', 'patched'),
        Case('msvc-integration', 'overlay'),
    ],
    'windows': [
        Case('windows-bootstrap', 'hello', failure='cycle in dependency graph'),
        Case('windows-bootstrap', 'hello', 'patched'),
    ],
}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('group', choices=GROUPS)
    args = parser.parse_args()
    failures = []
    for case in GROUPS[args.group]:
        command = [sys.executable, str(ROOT / 'run.py'), case.folder, '--case', case.name, '--variant', case.variant]
        if case.llvm_version:
            command += ['--llvm-version', case.llvm_version]
        if sys.platform == 'darwin':
            command.append('--host-sdk')
        if args.group in ('msvc', 'windows'):
            command.append('--accept-msvc-eula')
        result = subprocess.run(command, cwd=ROOT)
        variant_dir = case.variant + ('-' + case.llvm_version if case.llvm_version else '')
        log = (ROOT / 'results' / case.folder / variant_dir / (case.name + '.log')).read_text(errors='replace')
        passed = result.returncode == 0 if case.failure is None else result.returncode != 0 and re.search(case.failure, log, re.IGNORECASE) is not None
        label = f'{case.folder}/{case.name}/{variant_dir}'
        print(f'{"PASS" if passed else "FAIL"}: {label}', flush=True)
        print('\n'.join(log.splitlines()[-45:]), flush=True)
        if not passed:
            failures.append(label)
    if failures:
        print('Unexpected outcomes: ' + ', '.join(failures))
        return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
