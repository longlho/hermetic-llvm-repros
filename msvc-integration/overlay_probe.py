"""Show cwd-sensitive VFS backing paths without Cargo, SDK downloads, or private code."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def invoke(command, cwd):
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True)


def main():
    generator, clang = [str(Path(p).absolute()) for p in sys.argv[1:]]
    with tempfile.TemporaryDirectory(prefix='llvm-vfs-repro-') as temp:
        root = Path(temp).resolve() / 'fixture with spaces'
        (root / 'sdk').mkdir(parents=True)
        (root / 'overlays').mkdir()
        (root / 'consumer/nested').mkdir(parents=True)
        (root / 'sdk/Real.h').write_text('#define VALUE 42\n')
        (root / 'probe.c').write_text('#include <alias.h>\nint probe(void) { return VALUE; }\n')
        subprocess.run([generator, '-root', 'sdk', '-output', 'overlays/native.json'], cwd=root, check=True)
        data = json.loads((root / 'overlays/native.json').read_text())
        # A virtual-only alias prevents case-insensitive host filesystems from masking failure.
        def alias(node):
            if node['type'] == 'file':
                node['name'] = 'alias.h'
            for child in node.get('contents', []):
                alias(child)
        for node in data['roots']:
            alias(node)
        native = root / 'overlays/native.json'
        native.write_text(json.dumps(data))
        flags = [clang, '-fsyntax-only', '-ivfsoverlay', str(native), '-I', str(root / 'sdk'), str(root / 'probe.c')]
        control = invoke(flags, root)
        nested = invoke(flags, root / 'consumer/nested')
        # Positive control only: re-anchor the same public generator output, not an upstream patch.
        # LLVM parses roots as it encounters them: options must precede roots.
        data = {'version': 0, 'case-sensitive': False, 'root-relative': 'overlay-dir', 'overlay-relative': True, 'roots': data['roots']}
        def relocate(node, top=False):
            if top:
                node['name'] = '../' + node['name']
            if 'external-contents' in node:
                node['external-contents'] = '../' + node['external-contents']
            for child in node.get('contents', []):
                relocate(child)
        for node in data['roots']:
            relocate(node, True)
        native.write_text(json.dumps(data))
        relocated = root.with_name('moved fixture with spaces')
        shutil.move(root, relocated)
        fixed = invoke([clang, '-fsyntax-only', '-ivfsoverlay', str(relocated / 'overlays/native.json'), '-I', str(relocated / 'sdk'), str(relocated / 'probe.c')], relocated / 'consumer/nested')
        print(json.dumps({'original_cwd': control.returncode, 'nested_cwd': nested.returncode, 'relocated_overlay_control': fixed.returncode}))
        if control.returncode != 0 or nested.returncode == 0 or fixed.returncode != 0:
            print(control.stdout + control.stderr + nested.stdout + nested.stderr + fixed.stdout + fixed.stderr, file=sys.stderr)
            return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
