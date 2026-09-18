# Bindgen resource headers

**Issue:** 0.8.21 provides the merged Clang resource directory to link actions but omits it from compile arguments. Driver-independent consumers such as libclang/bindgen cannot always find builtin headers.

**Repro:** `probe.h` includes `<stddef.h>` and defines one struct containing `size_t`. `rules_rs` generates its Rust bindings while targeting Linux x86_64.

From the repo root on macOS with an installed SDK:

```sh
python3 run.py bindgen-resource-headers --case bindgen-linux --host-sdk
python3 run.py bindgen-resource-headers --case bindgen-linux --variant patched --host-sdk
```

**Observed:** unmodified 0.8.21 fails with `'stddef.h' file not found`; patched build succeeds and emits `probe.rs`. Native macOS `--case bindgen` succeeds unpatched, so the target platform matters.

**Upstream:** already fixed by merged [#755](https://github.com/hermeticbuild/hermetic-llvm/pull/755). `upstream-755.patch` is that public diff. This is release-backport evidence, not a reason to open a duplicate PR.
