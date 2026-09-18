# Public llvm-nm tool

**Question:** do consumers need a custom `@llvm//toolchain:llvm_nm` executable target?

**Repro:** compile a synthetic C symbol, invoke upstream `@llvm//tools:llvm-nm` from a custom Bazel action, capture output, and check that the symbol appears.

From the repo root on macOS with an installed SDK:

```sh
python3 run.py llvm-nm-target --case public --host-sdk
python3 run.py llvm-nm-target --case custom --host-sdk
```

**Observed:** `public` succeeds on unpatched 0.8.21 and finds `repro_exported_symbol`. `custom` references a downstream-only label; its absence upstream is not a compiler defect.

**Conclusion:** use the existing public tool. The consumer attribute must allow a source executable (`allow_single_file = True`) because the public target aliases a prebuilt executable. This shell-based fixture was validated on macOS, not native Windows. No upstream patch justified by this case.
