# iOS dynamic-library RPATH analysis

On a macOS worker with full Xcode selected, run:

```bash
python3 ios-rpaths/verify.py
```

The fixture builds a C dynamic library and a Rust executable that calls its
exported function, targeting the ARM64 iOS simulator. Bazel 9.2.0, Rust 1.96.0,
Apple Support 2.10.1, and the rules_rust revision bundled by rules_rs 0.0.111
are pinned. No application checkout, private archives, Cargo registry packages, or device
is required; the Apple SDK comes from Xcode.

Upstream `_compute_rpaths` rejects `target_os = ios` even though its Darwin
native-link dispatch already supports iOS. The one-line candidate admits iOS
to RPATH calculation and then performs the actual cross-link. The verifier
requires the exact upstream rejection followed by a successful patched build;
it does not execute the simulator program.

Local validation is unavailable on the Linux development host. The macOS CI job
checks both outcomes; a successful patched cross-link is pending that run.
