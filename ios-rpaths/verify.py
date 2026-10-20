"""Cross-link a real iOS Rust/C dynamic-library dependency on a macOS Xcode worker."""
import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--bazel", default="bazel")
args = parser.parse_args()
source = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix="ios-rpaths-") as temporary:
    work = Path(temporary)
    for name in ("MODULE.bazel", "BUILD.bazel", "native.c", "main.rs", "rules_rust_ios_rpaths.patch"):
        shutil.copy2(source / name, work / name)
    (work / ".bazelversion").write_text("9.2.0\n")
    module = (work / "MODULE.bazel").read_text()
    command = [args.bazel, "--nosystem_rc", "--nohome_rc", "--noworkspace_rc", "build", "//:hello", "--platforms=@apple_support//platforms:ios_sim_arm64", "--ios_minimum_os=15.0", "--jobs=4"]
    upstream = subprocess.run(command, cwd=work, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(upstream.stdout)
    if upstream.returncode == 0 or "Runtime linking is not supported on ios" not in upstream.stdout:
        raise SystemExit("FAIL: expected the iOS runtime-linking analysis rejection")
    (work / "MODULE.bazel").write_text(module.replace('use_repo(rules_rust, "rules_rust")', 'rules_rust.patch(patches = ["//:rules_rust_ios_rpaths.patch"], strip = 1)\nuse_repo(rules_rust, "rules_rust")'))
    patched = subprocess.run(command, cwd=work)
    if patched.returncode:
        raise SystemExit("FAIL: patched iOS Rust/C link")
    print("PASS: upstream rejection and patched real iOS Rust/C link")
