# MSVC headers, libraries, CRT, and VFS paths

This topic contains independent issues; it should not become one broad upstream PR.

| Case | Minimal probe | Interpretation |
| --- | --- | --- |
| `limits` | Include `<limits.h>`, use `_I64_MAX` | Missing MSVC C header export; upstream fails, candidate passes. |
| `legacy-stdio` | C object requests `legacy_stdio_definitions.lib` with `#pragma comment(lib, ...)` | Upstream cannot find the compatibility archive; the isolated library patch links successfully. |
| `stdio-mode` | C compilation rejects `_CRT_STDIO_ISO_WIDE_SPECIFIERS` | Policy probe only: upstream forces the macro on C; candidate restricts it to C++. Not proof of a runtime interoperability bug. |
| `crt-local` | Request static CRT with target-local features, reject `_DLL` | Upstream silently selects dynamic CRT. Patched configuration rejects the inconsistent request during analysis. |
| `crt-static` | Same source with graph-wide `crt_mode=static` | Public [PR #745](https://github.com/hermeticbuild/hermetic-llvm/pull/745) provides the setting; patched build succeeds. |
| `overlay` | Generate a VFS overlay, change cwd, then move the fixture | Original cwd passes; nested cwd fails; overlay-relative control passes after moving the fixture. No Cargo or real SDK needed. |

From the repo root on macOS with an installed SDK, after accepting Microsoft's runtime/SDK licenses:

```sh
python3 run.py msvc-integration --case limits --accept-msvc-eula --host-sdk
python3 run.py msvc-integration --case limits --variant patched --accept-msvc-eula --host-sdk
python3 run.py msvc-integration --case crt-local --accept-msvc-eula --host-sdk
python3 run.py msvc-integration --case crt-local --variant patched --accept-msvc-eula --host-sdk
python3 run.py msvc-integration --case crt-static --variant patched --accept-msvc-eula --host-sdk
python3 run.py msvc-integration --case overlay --host-sdk
```

Substitute `legacy-stdio` or `stdio-mode` for `limits` to compare their variants. These are macOS-hosted Windows cross-builds, not native Windows runtime tests.

`limits.patch`, `legacy-stdio.patch`, and `stdio-mode.patch` are independent candidates derived from public 0.8.21 source. The runner applies only the patch for the selected case. `crt-mode-745.patch` contains only the toolchain configuration portion of public PR #745; CRT selection is already tracked upstream in [#721](https://github.com/hermeticbuild/hermetic-llvm/issues/721).

The overlay harness uses a virtual-only header alias so a case-insensitive filesystem cannot hide lookup failures. Its positive control re-anchors public generator output relative to the overlay and moves the entire fixture, including spaces in the path. That control demonstrates the needed semantics; it is not a production generator patch. See root `RESULTS.md` for completed runs and precise status.
