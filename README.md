# hermetic-llvm standalone repros

Small public-source experiments against pinned official hermetic-llvm releases, using Bazel 9.2.0. Folders isolate individual compiler and build-rule integration topics. A policy assertion is not proof of an upstream defect.

| Folder | Question |
| --- | --- |
| `bindgen-resource-headers` | Does a driver-independent bindgen consumer receive compiler builtin headers? |
| `macos-go-link` | Do Go platform/exec transitions lose a compiler-rt archive path? Are public directory providers sufficient? |
| `msvc-integration` | Which CRT, header, library, and VFS assumptions fail independently? |
| `windows-hardlinks` | Do relative tool symlinks fail on Windows container bind mounts, and do hardlinks fix them? |
| `windows-bootstrap` | Does native Windows compilation depend on its own SDK overlay generator? |

The Rust fixtures pin **LLVM 0.8.25**, **rules_rs 0.0.111**, and **Rust 1.96.0**:

| Folder | Question |
| --- | --- |
| `rust-android-eabi` | Does Cargo dependency resolution recognize Android ARMv7 cfg attributes? |
| `rust-msvc-linker` | Can Rust cross-link C on MSVC, and do Cargo scripts receive target flags? |
| `ios-rpaths` | Can Rust cross-link a real iOS C dynamic-library dependency? |

Run `python3 verify-rust-cross.py android --ndk-home /path/to/ndk`,
`python3 verify-rust-cross.py msvc --accept-msvc-eula`, or
`python3 verify-rust-cross.py msvc-crt --accept-msvc-eula` on Linux x86-64.
Run `python3 ios-rpaths/verify.py` on macOS with Xcode. These check precise
upstream failures and candidate successes; they do not run target programs.
Rust upstream patch context retains its Apache 2.0 license in `RUST-UPSTREAM-LICENSE`.

## Run

Install Bazel 9.2.0 (or Bazelisk), Python 3.10+, and Git. Run from this repository:

```sh
python3 run.py macos-go-link --case exec-transition --host-sdk
python3 run.py bindgen-resource-headers --case bindgen-linux --host-sdk
python3 run.py msvc-integration --case limits --accept-msvc-eula --host-sdk
python3 run.py msvc-integration --case limits --variant patched --accept-msvc-eula --host-sdk
```

`--host-sdk` is a macOS-only option using an installed Xcode/Command Line Tools SDK; omit it elsewhere. This intentionally avoids conflating SDK archive availability with compiler behavior. Windows target tests require explicit acceptance of the Microsoft runtime and SDK licenses. `--bazel /path/to/bazel` chooses an executable. No user/system Bazel configs, remote execution, or remote caches are imported.

For the native Windows cycle, run in PowerShell on Windows x64, with Git Bash installed:

```powershell
./run-windows.ps1 -Variant upstream -AcceptMsvcEula -AnalyzeOnly -MsvcHost
./run-windows.ps1 -Variant patched -AcceptMsvcEula -AnalyzeOnly -MsvcHost
```

Remove `-AnalyzeOnly` to compile. `-Bazel` selects Bazel; optional `-OutputUserRoot C:/b` gives Windows a short output path. Analysis results are not runtime proof.

Each variant gets its own ignored `.work/` workspace. `upstream` uses the unmodified release. `patched` adds only that folder's candidate changes. Exit codes and raw logs are local under ignored `results/`; never publish those logs without manual review. Checked-in findings contain only sanitized diagnostics and platform descriptions.

## Provenance

Fixtures are synthetic. Candidate diffs were derived from public upstream source; `crt-mode-745.patch` comes from the linked public upstream PR. The obsolete bindgen backport was removed after upgrading to 0.8.24. No application checkout, private package, private Bazel configuration, or private build log is required. Public upstream code retains its MIT license in `UPSTREAM-LICENSE`.

See [RESULTS.md](RESULTS.md) for observed outcomes and limits. Repros that pass upstream remain useful negative controls; they should not be submitted as upstream bugs.

## Release regression checks

`python3 verify-release.py bindgen`, `go`, or `msvc` checks exact baseline and candidate outcomes on macOS ARM64. `python verify-release.py windows` checks native Windows bootstrap. The separate Windows hardlink workflow tests process-isolated container bind mounts. These public-source workflows print test diagnostics; earlier local raw logs remain ignored.
