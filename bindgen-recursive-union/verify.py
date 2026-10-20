#!/usr/bin/env python3
"""Verify exact upstream panic and candidate success using public pinned sources."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = Path(__file__).resolve().parent
RELEASES = {
    "0.72.1": "993776b509cfb49c750f11b8f07a46fa23e0a1386ffc01fb1e7d343efc387895",
    "0.73.2": "787ef8ef523575546b106a58213d6e6b06198a05c2f757258c68a74273670cfa",
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cargo", default="cargo")
    parser.add_argument("--version", choices=["all", *RELEASES], default="all")
    args = parser.parse_args()
    versions = RELEASES if args.version == "all" else [args.version]
    failed = []
    for version in versions:
        work = ROOT / ".work" / "bindgen-recursive-union" / version
        work.mkdir(parents=True, exist_ok=True)
        archive = work / "bindgen.crate"
        if not archive.exists():
            urllib.request.urlretrieve(f"https://static.crates.io/crates/bindgen/bindgen-{version}.crate", archive)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != RELEASES[version]:
            raise RuntimeError("pinned bindgen archive checksum mismatch")
        for variant in ("upstream", "patched"):
            project = work / variant
            source = project / "bindgen"
            if project.exists():
                shutil.rmtree(project)
            source.mkdir(parents=True)
            with tarfile.open(archive) as tar:
                for member in tar:
                    relative = Path(*Path(member.name).parts[1:])
                    destination = source / relative
                    destination.resolve().relative_to(source.resolve())
                    if member.isdir():
                        destination.mkdir(parents=True, exist_ok=True)
                    elif member.isfile():
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        destination.write_bytes(tar.extractfile(member).read())
                    else:
                        raise RuntimeError("unexpected archive member type")
            for name in ("main.rs", "probe.hpp"):
                shutil.copy2(FIXTURE / name, project / name)
            manifest = (FIXTURE / "Cargo.toml").read_text().replace('=0.72.1', '=' + version)
            manifest += '\n[patch.crates-io]\nbindgen = { path = "bindgen" }\n'
            (project / "Cargo.toml").write_text(manifest)
            if variant == "patched":
                subprocess.run(["patch", "-p1", "-i", str(FIXTURE / "template-layout.patch")], cwd=source, check=True, stdout=subprocess.DEVNULL)
            result_dir = ROOT / "results" / "bindgen-recursive-union" / version
            result_dir.mkdir(parents=True, exist_ok=True)
            log_path = result_dir / (variant + ".log")
            environment = dict(os.environ, CARGO_TARGET_DIR=str(work / "target"))
            with log_path.open("w") as log:
                result = subprocess.run([args.cargo, "run", "--quiet", "--manifest-path", str(project / "Cargo.toml")], env=environment, stdout=log, stderr=subprocess.STDOUT)
            log = log_path.read_text(errors="replace")
            passed = result.returncode == 0 if variant == "patched" else result.returncode != 0 and "Not an item: ItemId(" in log
            label = f"bindgen {version}/{variant}"
            print(f'{"PASS" if passed else "FAIL"}: {label} (exit {result.returncode})', flush=True)
            if not passed:
                failed.append(label)
                print("\n".join(log.splitlines()[-30:]))
    if failed:
        print("Unexpected outcomes: " + ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
