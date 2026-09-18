# Measured results

Validated 2026-09-18 with Bazel 9.2.0 and official hermetic-llvm 0.8.21. User/system Bazel configs disabled. macOS tests used an installed SDK; Windows tests used the declared Microsoft SDK/runtime repositories. No private build configuration, remote execution, or remote cache was used.

| Folder / case | Upstream | Candidate / control | Conclusion |
| --- | --- | --- | --- |
| Bindgen, Linux x86_64 target from macOS ARM64 | Fails: `'stddef.h' file not found` | Public #755 passes | Independent reproduction; already fixed upstream, awaiting release. |
| Bindgen, native macOS target | Passes | Not needed | Platform-sensitive negative control. |
| macOS Go platform transition | Passes | Not needed | No defect reproduced. |
| macOS Go executable/tool transition | Builds and executes successfully | Not needed | No defect reproduced even with non-legacy platform output paths. |
| macOS public header directory | Passes | Not needed | Existing public provider is sufficient. |
| macOS private directory helper | Visibility error | Public provider passes | Invalid private-target usage, not an upstream defect. |
| MSVC `limits.h` | `_I64_MAX` undeclared | `limits.patch` passes | Independent missing-header reproduction. |
| MSVC compatibility archive | Cannot open `legacy_stdio_definitions.lib` | `legacy-stdio.patch` passes | Independent missing-library reproduction. |
| MSVC C stdio mode | Compile-time policy assertion fails | `stdio-mode.patch` passes | Demonstrates macro policy only; no runtime ABI conflict established. |
| Target-local static CRT feature | `_DLL` still defined | Public #745 rejects incompatible target-local feature during analysis | Confirms silent configuration mismatch; already has upstream PR. |
| Graph-wide static CRT | Setting absent in 0.8.21 | Public #745 builds with static mode | Positive control for supported configuration. |
| VFS cwd/relocation | Original cwd passes; nested cwd cannot find virtual header | Overlay-relative positive control passes after moving fixture | Independent cwd-sensitive overlay reproduction; control is not a production generator patch. |
| Native Windows, default host platform | Analysis and build pass | Not needed | Negative control; target ABI alone does not trigger the cycle. |
| Native Windows, explicit MSVC host | Analysis fails with SDK-overlay generator dependency cycle | Stage-0 + hosted-stage-1 exclusion passes analysis and compilation | Independent native-host bootstrap cycle. |
| Public `@llvm//tools:llvm-nm` | Extracts synthetic exported symbol | Not needed | No custom target required for tested consumer. |

## Windows candidate boundary

Excluding overlays only for hosted stage 1 leaves a second cycle through stage-0 compiler-rt. The isolated candidate excludes both stages. Default-host success must not be reported as proof for explicit MSVC-host execution.

Patched explicit-MSVC-host compilation succeeds: 393 actions, producing `hello.exe` on Windows x64. Running that executable exits 0.

## What is ready for upstream discussion

- Bootstrap cycle, missing `limits.h`, missing compatibility library: independent minimal failures with candidate fixes.
- VFS paths: independent failure and relocated positive control; production generator/interface changes remain to be designed and tested.
- Bindgen and CRT selection: attach evidence to existing #755 / #745 work rather than duplicate it.
- Go builtins linking, helper visibility, custom llvm-nm alias: no upstream necessity established by these repros.
- C stdio policy: requires a real interoperability/runtime example before presenting it as an upstream bug.

Raw machine logs and build outputs are intentionally not committed. An unrelated download, missing executable, license gate, or patch-application error is not a reproduced compiler/toolchain defect.
