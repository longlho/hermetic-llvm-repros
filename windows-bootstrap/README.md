# Native Windows overlay bootstrap cycle

**Suspected issue:** the Windows toolchain consumes generated SDK overlays while compiling the generator that produces them, creating a dependency cycle.

**Repro:** an otherwise empty `cc_binary` on a native Windows x64 host, using only the official 0.8.21 module. No Rust, Cargo, or application build rules are involved.

From the repo root in Windows PowerShell, with Bazel and Git Bash installed, after reviewing the Microsoft runtime/SDK licenses:

```powershell
./run-windows.ps1 -Variant upstream -AcceptMsvcEula -AnalyzeOnly
./run-windows.ps1 -Variant patched -AcceptMsvcEula -AnalyzeOnly
```

Expected confirmation: upstream analysis reports a dependency cycle involving the SDK overlay generator; patched analysis succeeds. A different error is an infrastructure/setup failure, not a reproduction. Remove `-AnalyzeOnly` to compile the executable; a successful analysis alone does not establish successful compilation or execution.

**Candidate:** `bootstrap.patch` excludes header/library overlay inputs only for stage-1 hosted bootstrap tools. Ordinary targets retain overlays. It is derived directly from public release source and contains no Cargo-specific additions.

**Status:** native Windows validation in progress; see root `RESULTS.md`. Cross-compilation on macOS cannot validate this native-host cycle.
