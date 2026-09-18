# Public llvm-nm tool

**Status: retired patch.** The public upstream tool already covers this use. Keep this folder as a passing regression control; no upstream PR is needed.

**Repro:** compile a synthetic C symbol, invoke upstream `@llvm//tools:llvm-nm` from a custom Bazel action, capture output, and check that the symbol appears.

From the repo root on macOS with an installed SDK:

```sh
python3 run.py llvm-nm-target --case public --host-sdk
```

**Observed:** `public` succeeds on unpatched 0.8.21 and finds `repro_exported_symbol`. The obsolete custom-target case has been removed.

**Conclusion:** use the existing public tool. The consumer attribute must allow a source executable (`allow_single_file = True`) because the public target aliases a prebuilt executable. This shell-based fixture was validated on macOS, not native Windows. No upstream patch justified by this case.
