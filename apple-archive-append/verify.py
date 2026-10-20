#!/usr/bin/env python3
"""Prove apple_support ar-compatible wrapper loses cc-rs archive batches."""
import argparse
import hashlib
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import urllib.request

SOURCE_URL = "https://raw.githubusercontent.com/bazelbuild/apple_support/2.10.1/crosstool/libtool.cc"
SOURCE_SHA256 = "d8bcfbeb1b37b7d14f4c820ff80032a481e9dc4e64ce7245bdd47f74cf2ef79a"
HERE = Path(__file__).resolve().parent


def run(args, **kwargs):
    return subprocess.run([str(x) for x in args], check=True, text=True, **kwargs)


def output(args, **kwargs):
    return run(args, stdout=subprocess.PIPE, **kwargs).stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command-only", action="store_true", help="Verify wrapper translation without requiring an Apple SDK")
    parser.add_argument("--llvm-ar", default=os.environ.get("LLVM_AR"), help="Declared LLVM archiver to compare against the wrapper")
    args = parser.parse_args()
    if not args.command_only and platform.system() != "Darwin":
        parser.error("archive/link verification requires macOS; use --command-only elsewhere")
    with tempfile.TemporaryDirectory(prefix="apple-archive-append-") as temporary:
        work = Path(temporary)
        source = work / "libtool.cc"
        data = urllib.request.urlopen(SOURCE_URL).read()
        assert hashlib.sha256(data).hexdigest() == SOURCE_SHA256, "Upstream source checksum changed"
        source.write_bytes(data)
        wrapper = work / "apple-libtool-wrapper"
        run(["c++", "-std=c++17", source, "-o", wrapper])
        archive = work / "already-existing.a"
        archive.write_bytes(b"!<arch>\n")
        environment = dict(os.environ, DEVELOPER_DIR=temporary, SDKROOT=temporary, __LIBTOOL_LOG_ONLY="1")
        invocation = output([wrapper, "cq", archive, work / "last.o"], env=environment)
        assert invocation.count(str(archive)) == 1, invocation
        assert "libtool -static -D -o" in invocation, invocation
        print("PASS: cq of existing archive translates to replacement with no previous archive input", flush=True)
        print(invocation, flush=True)
        if args.command_only:
            return
        llvm_ar = args.llvm_ar
        if not llvm_ar:
            host = output(["rustc", "-vV"]).split("host: ")[1].splitlines()[0]
            llvm_ar = str(Path(output(["rustc", "--print", "sysroot"])) / "lib/rustlib" / host / "bin/llvm-ar")
        assert Path(llvm_ar).is_file(), "Install rustup component llvm-tools-preview or set LLVM_AR"
        sdk = output(["xcrun", "--sdk", "iphonesimulator", "--show-sdk-path"])
        developer = output(["xcode-select", "-p"])
        arch = "aarch64" if platform.machine() == "arm64" else "x86_64"
        rust_target = f"{arch}-apple-ios" + ("-sim" if arch == "aarch64" else "")
        clang_target = ("arm64" if arch == "aarch64" else arch) + "-apple-ios15.0-simulator"
        cc = output(["xcrun", "--find", "clang"])
        source_directory = work / "objects"
        source_directory.mkdir()
        for i in range(101):
            (source_directory / f"unit_{i:03}.c").write_text(f"int aws_lc_probe_{i:03}(void) {{ return {i}; }}\n")
        main_source = work / "main.c"
        main_source.write_text("int aws_lc_probe_000(void); int aws_lc_probe_100(void); int main(void) { return aws_lc_probe_000() + aws_lc_probe_100() - 100; }\n")
        for name, archiver, expected_members in [("wrapper", wrapper, 1), ("llvm", llvm_ar, 101)]:
            crate = work / name
            crate.mkdir()
            for item in ("Cargo.toml", "build.rs"):
                shutil.copy(HERE / item, crate / item)
            shutil.copytree(HERE / "src", crate / "src")
            environment = dict(os.environ, PROBE_TARGET=rust_target, PROBE_SOURCE=str(source_directory),
                               AR=str(archiver), ARFLAGS="", CC=cc, SDKROOT=sdk, DEVELOPER_DIR=developer,
                               CFLAGS=f"-target {clang_target} -isysroot {sdk}", CARGO_TARGET_DIR=str(crate / "target"))
            run(["cargo", "build", "--manifest-path", crate / "Cargo.toml"], env=environment)
            archives = list((crate / "target/debug/build").glob("*/out/libprobe.a"))
            assert len(archives) == 1, archives
            native = archives[0]
            members = output(["xcrun", "ar", "t", native]).splitlines()
            assert len(members) == expected_members, (name, len(members), members)
            symbols = output(["xcrun", "nm", "-g", native])
            assert "_aws_lc_probe_100" in symbols
            assert ("_aws_lc_probe_000" in symbols) == (name == "llvm")
            command = [cc, "-target", clang_target, "-isysroot", sdk, main_source, native, "-o", work / f"{name}.exe"]
            link = subprocess.run([str(x) for x in command], text=True, capture_output=True)
            if name == "wrapper":
                assert link.returncode != 0 and "_aws_lc_probe_000" in link.stderr, link.stderr
                print("PASS: wrapper retains only final object; iOS simulator link fails with missing first C symbol", flush=True)
                print(link.stderr, flush=True)
            else:
                assert link.returncode == 0, link.stderr
                print("PASS: llvm-ar retains all 101 objects; identical iOS simulator link succeeds", flush=True)
        print("3 regression checks passed", flush=True)


if __name__ == "__main__":
    main()
