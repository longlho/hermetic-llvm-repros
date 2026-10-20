# Android EABI Cargo dependency resolution

Pins Bazel 9.2.0, rules_rs 0.0.111, Rust 1.96.0, LLVM 0.8.25,
rules_android_ndk 0.1.5, NDK 29.0.14206865, and Android API 26.

```sh
python3 verify-rust-cross.py android --ndk-home /path/to/android-ndk-r29
```

Install the NDK from Google's official repository metadata:
<https://dl.google.com/android/repository/repository2-1.xml>.
Its Linux archive is `android-ndk-r29-linux.zip`, 783549481 bytes,
SHA-1 `87e2bb7e9be5d6a1c6cdf5ec40dd4e0c6d07c30b`.
The verifier mounts an NDK under `/tmp` into Bazel's isolated temporary directory.

The fixture builds the public socket2 0.5.10 library. Its `cfg(unix)` dependency
on libc is missing upstream for `armv7-linux-androideabi`: rules_rs derives
`target_os=androideabi`, `target_arch=armv7`, and `target_vendor=linux`.
`rustc --print cfg --target armv7-linux-androideabi` reports Android, ARM,
unknown vendor, and EABI. The candidate normalizes those attributes.

On Linux x86-64, the verifier observes missing-libc compilation errors upstream
and successful compilation with only the candidate patch. It checks the exact
diagnostic family, so a download, license, or tool error cannot count as proof.
This proves dependency resolution and compilation, not Android runtime behavior.

Source: [rules_rs cfg derivation](https://github.com/hermeticbuild/rules_rs/blob/v0.0.111/rs/private/cfg_parser.bzl).
