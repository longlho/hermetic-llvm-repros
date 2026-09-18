# macOS Go linking and SDK visibility

**Suspected issue:** a raw compiler-rt archive path might become invalid across Go/Bazel configuration transitions. A separate visibility change would expose helper targets created by `headers_directory`.

**Repro:** tiny cgo executable calling a C function, built through a macOS ARM64 transition and then executed as a build tool. Separate directory fixtures compare the public provider with its private helper target.

From the repo root on macOS ARM64 with an installed SDK:

```sh
python3 run.py macos-go-link --case transitioned --host-sdk
python3 run.py macos-go-link --case exec-transition --host-sdk
python3 run.py macos-go-link --case public-headers --host-sdk
python3 run.py macos-go-link --case internal-headers --host-sdk
```

**Observed on unpatched 0.8.21:** both Go transition cases succeed, including with the non-legacy platform output layout. `public-headers` succeeds; `internal-headers` fails because it deliberately references a private implementation target.

**Conclusion:** no independent Go-link failure reproduced. Public `headers_directory` already supports `directory_glob`; exposing private helpers is not necessary for this use. `go-builtins.patch` is an experimental `-L`/`-l` alternative, not a demonstrated required fix. Do not open an upstream bug on this evidence alone. The profile-runtime naming issue is already handled in 0.8.21 and needs no patch here.
