"""Build public Rust cross-target fixtures and check exact before/after outcomes."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("group", choices=["android", "msvc", "msvc-crt", "ring"])
    parser.add_argument("--bazel", default="bazel")
    parser.add_argument("--ndk-home", type=Path)
    parser.add_argument("--accept-msvc-eula", action="store_true")
    args = parser.parse_args()
    if args.group == "android" and not args.ndk_home:
        parser.error("android requires --ndk-home pointing to an installed NDK 29.0.14206865")
    if args.group in ("msvc", "msvc-crt", "ring") and not args.accept_msvc_eula:
        parser.error("msvc requires --accept-msvc-eula for the Microsoft runtime/SDK repositories")
    if args.group == "android":
        folder = "rust-android-eabi"
        cases = [("armv7", "upstream"), ("armv7", "patched")]
        candidate = 'single_version_override(module_name = "rules_rs", patches = ["//:rules_rs_android_eabi_cfg.patch"], patch_strip = 1)'
        expected_failure = r"(?:unresolved import|unresolved module or unlinked crate).*libc"
    elif args.group == "ring":
        folder = "rust-ring-arm64"
        cases = [("arm64", "upstream"), ("arm64", "patched")]
        candidate = 'crate.annotation(crate = "ring", repositories = ["probe_crates"], patches = ["//:ring-windows-arm64-clang-cl.patch"], patch_args = ["-p1"])'
        expected_failure = r'failed to find tool "clang"'
    elif args.group == "msvc-crt":
        folder = "rust-msvc-linker"
        cases = [(arch, variant) for arch in ["x64", "arm64"] for variant in ["upstream", "patched"]]
        candidate = 'rules_rust.patch(patches = ["//:rules_rust_build_script_target_cfg.patch"], strip = 1)'
        expected_failure = r"target cfg omits crt-static"
    else:
        folder = "rust-msvc-linker"
        cases = [(arch, variant) for arch in ["x64", "arm64"] for variant in ["upstream", "patched"]]
        candidate = 'rules_rust.patch(patches = ["//:rules_rust_msvc_linker.patch"], strip = 1)'
        expected_failure = r"clang-cl: error: no such file or directory: '/(?:LIBPATH|PDBALTPATH)"
    failures = []
    for arch, variant in cases:
        name = args.group + "-" + arch + "-" + variant
        workspace = ROOT / ".work" / "rust-cross" / name
        output = ROOT / ".work" / "rust-cross-output" / name
        if workspace.exists():
            shutil.rmtree(workspace)
        shutil.copytree(ROOT / folder, workspace)
        module = workspace / "MODULE.bazel"
        module.write_text(module.read_text().replace("# CANDIDATE_PATCH", candidate if variant == "patched" else ""))
        command = [args.bazel, "--nosystem_rc", "--nohome_rc", "--noworkspace_rc", "--output_base=" + str(output), "build", "--jobs=4", "--verbose_failures"]
        if args.group == "android":
            ndk = args.ndk_home.resolve()
            command += ["@probe_crates//:socket2-0.5.10", "--host_platform=@rules_rs//rs/platforms:x86_64-unknown-linux-gnu", "--platforms=@rules_rs//rs/platforms:armv7-linux-androideabi", "--repo_env=ANDROID_NDK_HOME=" + str(ndk)]
            if sys.platform == "linux" and str(ndk).startswith("/tmp/"):
                command += ["--sandbox_add_mount_pair=" + str(ndk)]
        else:
            command += ["@probe_crates//:ring-0.17.14" if args.group == "ring" else ("//:crt_probe" if args.group == "msvc-crt" else "//:probe"), "--host_platform=//:local_gnu", "--platforms=//:windows_" + arch, "--repo_env=BAZEL_MSVC_RUNTIME_VISUAL_STUDIO_EULA=1"]
        result_dir = ROOT / "results" / "rust-cross"
        result_dir.mkdir(parents=True, exist_ok=True)
        log_path = result_dir / (name + ".log")
        with log_path.open("w") as log:
            result = subprocess.run(command, cwd=workspace, stdout=log, stderr=subprocess.STDOUT)
        text = log_path.read_text(errors="replace")
        passed = result.returncode == 0 if variant == "patched" else result.returncode != 0 and re.search(expected_failure, text, re.IGNORECASE) is not None
        print(("PASS" if passed else "FAIL") + ": " + name + " (exit " + str(result.returncode) + ")", flush=True)
        print("\n".join(text.splitlines()[-12:]), flush=True)
        if not passed:
            failures.append(name)
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
