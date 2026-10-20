# Rust MSVC linker and build-script target flags

Pins Bazel 9.2.0, rules_rs 0.0.111, Rust 1.96.0, LLVM 0.8.25, and
windows_support 0.4.1. rules_rs selects rules_rust source revision
`00f8db0ed456a59c5bf0643692cc5b30e564018e`. The fixtures need only public sources and the declared
Microsoft SDK/runtime repositories. Accept their licenses explicitly:

```sh
python3 verify-rust-cross.py msvc --accept-msvc-eula
python3 verify-rust-cross.py msvc-crt --accept-msvc-eula
```

The linker case builds a native C function into a Rust executable for Windows
x64 and ARM64. Upstream passes rustc's raw `/LIBPATH` and `/PDBALTPATH` arguments
to `clang-cl`, which treats them as filenames. The independent candidate selects
the corresponding `lld-link` and preserves linker arguments while excluding
compiler-driver flags. Both unpatched targets fail with that exact diagnostic;
both patched targets cross-link. PE headers identify AMD64 and ARM64 outputs.

The separate CRT case configures `-Ctarget-feature=+crt-static` and asks a real
Cargo build script to inspect `CARGO_CFG_TARGET_FEATURE`. Upstream omits that
feature because it queries `rustc --print cfg` without the configured flags.
The candidate propagates extra target flags into Cargo's encoded flags and
uses them for the cfg query. No provider library or application is involved.

Static CRT selection uses two Bazel flags, `--features=-dynamic_link_msvcrt`
and `--features=static_link_msvcrt`; a comma-separated string is one feature.
These are Linux-hosted cross-builds; no Windows executable is run.

Source: [link configuration](https://github.com/hermeticbuild/rules_rust/blob/00f8db0ed456a59c5bf0643692cc5b30e564018e/rust/private/rustc.bzl),
[Cargo cfg query](https://github.com/hermeticbuild/rules_rust/blob/00f8db0ed456a59c5bf0643692cc5b30e564018e/cargo/private/cargo_build_script_runner/bin.rs).
