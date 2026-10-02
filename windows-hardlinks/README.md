# Windows archive tool links

The LLVM 0.8.21 minimal Windows archive uses relative symlinks from tool names to `llvm.exe`. This experiment tests replacing those links with hardlinks during Bazel repository extraction.

```powershell
./windows-hardlinks/run.ps1
./windows-hardlinks/run.ps1 -Container
```

Requires Windows x64, Bazel 9.2.0, and symlink creation privileges. The container case additionally requires a Windows Server 2022 host and Docker running Windows containers. GitHub Actions runs both cases on `windows-2022`.

Each variant uses a separate Bazel workspace with `--windows_enable_symlinks`; without this flag Bazel copies file symlinks, hiding the behavior under test. The actual upstream extension fetches its checksum-pinned archive. The patched variant applies `hardlinks.patch` to the extension, exercising Bazel's `patch_cmds_win` execution rather than invoking a substitute script.

Assertions:

- Upstream archive retains file symlinks; patched archive has none.
- Patched `clang-cl.exe` and `lld-link.exe` share hardlink identity with `llvm.exe`.
- Both host variants launch the compiler/linker and compile a header-free C file.
- Both repositories are mounted at their physical repository-cache path. Upstream must retain a relative tool link and fail with Windows error 3; patched launch must succeed. Resolving the external-directory junction avoids confusing missing cache paths with the relative-link defect.
- A separate fixture uses the same real `llvm.exe` with an explicitly relative `clang-cl.exe` symlink. It launches on the host, must fail with Windows error 3 on a container bind mount, then must launch after the exact command from the patch converts it to a hardlink.
- Conversion tolerates a changed PowerShell location and a second invocation. Unexpected baseline success or any unrelated failure fails the test.

The container test covers a Docker bind mount, not a Kubernetes PVC. Host-only success does not reproduce the container defect. It does not test ARM64, a full SDK build, or arbitrary symlink graphs. Public upstream source remains covered by `../UPSTREAM-LICENSE`. No application source or private build configuration is used.
