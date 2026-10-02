# Windows archive tool links

The LLVM 0.8.21 minimal Windows archive uses relative symlinks from tool names to `llvm.exe`. This experiment tests replacing those links with hardlinks during Bazel repository extraction.

```powershell
./windows-hardlinks/run.ps1
./windows-hardlinks/run.ps1 -Container
```

Requires Windows x64, Bazel 9.2.0, and symlink creation privileges. The container case additionally requires a Windows Server 2022 host and Docker running Windows containers. GitHub Actions runs both cases on `windows-2022`.

Each variant uses a separate Bazel workspace. The actual upstream extension fetches its checksum-pinned archive. The patched variant applies `hardlinks.patch` to the extension, exercising Bazel's `patch_cmds_win` execution rather than invoking a substitute script.

Assertions:

- Upstream archive retains file symlinks; patched archive has none.
- Patched `clang-cl.exe` and `lld-link.exe` share hardlink identity with `llvm.exe`.
- Both host variants launch the compiler/linker and compile a header-free C file.
- In a process-isolated container with the repository bind-mounted, upstream `CreateProcessW` must fail with Windows error 3. Patched launch must succeed. Other failures, or a baseline that succeeds, fail the test.

The container test covers a Docker bind mount, not a Kubernetes PVC. Host-only success does not reproduce the container defect. It does not test ARM64, a full SDK build, or arbitrary symlink graphs. Public upstream source remains covered by `../UPSTREAM-LICENSE`. No application source or private build configuration is used.
