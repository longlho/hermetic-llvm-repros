# Native Windows overlay bootstrap cycle

**Suspected issue:** the Windows toolchain consumes generated SDK overlays while compiling the generator that produces them, creating a dependency cycle.

**Repro:** an otherwise empty `cc_binary` on a native Windows x64 host, using only the official 0.8.21 module and explicitly selecting `--host_platform=@llvm//platforms:windows_x86_64_msvc`. No Rust, Cargo, or application build rules are involved.

From the repo root in Windows PowerShell, with Bazel and Git Bash installed, after reviewing the Microsoft runtime/SDK licenses:

```powershell
./run-windows.ps1 -Variant upstream -AcceptMsvcEula -AnalyzeOnly -MsvcHost
./run-windows.ps1 -Variant patched -AcceptMsvcEula -AnalyzeOnly -MsvcHost
```

Expected confirmation: upstream analysis reports a dependency cycle involving the SDK overlay generator; patched analysis succeeds. A different error is an infrastructure/setup failure, not a reproduction. Remove `-AnalyzeOnly` to compile the executable; a successful analysis alone does not establish successful compilation or execution.

**Candidate:** `bootstrap.patch` excludes header/library overlay inputs for stage-0 runtime builds and stage-1 hosted bootstrap tools. Ordinary targets retain overlays. It is derived directly from public release source and contains no Cargo-specific additions.

**Observed:** clean native Windows analysis with an MSVC host fails with an SDK overlay generator dependency cycle. The default host selection analyzes and builds successfully, so explicit host ABI selection is essential. Excluding only stage-1 hosted tools leaves a second cycle through stage-0 compiler-rt; the candidate also excludes that stage. The corrected candidate passes native Windows analysis and compiles `hello.exe`, which exits 0 when run. See root `RESULTS.md` for the full matrix. Cross-compilation on macOS cannot validate this native-host cycle.
