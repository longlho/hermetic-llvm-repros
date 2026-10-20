# ring Windows ARM64 compiler selection

ring 0.17.14 `build.rs:563` replaces the explicitly configured compiler with bare
`clang` on Windows ARM64 when cc-rs reports that compiler as clang-cl. In a Bazel
sandbox this fails because `clang` is not on PATH. The candidate recognizes
clang-cl as an existing Clang compiler and retains the hermetic toolchain.

```sh
python3 verify-rust-cross.py ring --accept-msvc-eula
```

The negative check requires the exact missing-`clang` error. The positive check
builds ring's complete ARM64 native library and Rust bindings with the same
version and crypto implementation. This checks compilation, not ARM64 execution.
Versions match the other Rust fixtures: Bazel 9.2.0, rules_rs 0.0.111,
Rust 1.96.0, hermetic-llvm 0.8.25, windows_support 0.4.1.

Source: [ring 0.17.14 build script](https://github.com/briansmith/ring/blob/0.17.14/build.rs#L563).
