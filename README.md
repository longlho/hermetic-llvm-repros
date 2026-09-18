# hermetic-llvm standalone repros

Small public-source experiments against the official **hermetic-llvm 0.8.21** release, using Bazel 9.2.0. Four folders track the remaining investigated patch topics. A policy assertion is not proof of an upstream defect.

| Folder | Question |
| --- | --- |
| `bindgen-resource-headers` | Does a driver-independent bindgen consumer receive compiler builtin headers? |
| `macos-go-link` | Do Go platform/exec transitions lose a compiler-rt archive path? Are public directory providers sufficient? |
| `msvc-integration` | Which CRT, header, library, and VFS assumptions fail independently? |
| `windows-bootstrap` | Does native Windows compilation depend on its own SDK overlay generator? |

## Run

Install Bazel 9.2.0 (or Bazelisk), Python 3.10+, and Git. Run from this repository:

```sh
python3 run.py macos-go-link --case exec-transition --host-sdk
python3 run.py bindgen-resource-headers --case bindgen-linux --host-sdk
python3 run.py bindgen-resource-headers --case bindgen-linux --variant patched --host-sdk
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

Fixtures are synthetic. Candidate diffs were derived from public upstream 0.8.21 source, except `upstream-755.patch` and `crt-mode-745.patch`, taken from the linked public upstream PRs. No application checkout, private package, private Bazel configuration, or private build log is required. Public upstream code retains its MIT license in `UPSTREAM-LICENSE`.

See [RESULTS.md](RESULTS.md) for observed outcomes and limits. Repros that pass upstream remain useful negative controls; they should not be submitted as upstream bugs.
