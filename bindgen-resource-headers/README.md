# Bindgen resource headers

**Issue:** 0.8.21 provides the merged Clang resource directory to link actions but omits it from compile arguments. Driver-independent consumers such as libclang/bindgen cannot always find builtin headers.

**Repro:** `probe.h` includes `<stddef.h>` and defines one struct containing `size_t`. `rules_rs` generates its Rust bindings while targeting Linux x86_64.

From the repo root on macOS with an installed SDK:

```sh
python3 run.py bindgen-resource-headers --case bindgen-linux --host-sdk
```

**Observed:** unmodified 0.8.21 fails with `'stddef.h' file not found`; patched build succeeds and emits `probe.rs`. Native macOS `--case bindgen` succeeds unpatched, so the target platform matters.

**Upstream:** already fixed by merged [#755](https://github.com/hermeticbuild/hermetic-llvm/pull/755). The backport was removed when this repo upgraded to 0.8.24: native macOS and Linux cross-target cases both pass unpatched. Historical failing 0.8.21 fixtures remain in Git history.
