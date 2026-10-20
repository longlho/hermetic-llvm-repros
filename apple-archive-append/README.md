# Apple ar compatibility loses archive batches

`apple_support` 2.10.1's libtool wrapper accepts `ar cq`, but translates it to
`xcrun libtool -static -D -o output.a new-objects...`. It omits the existing
archive from the inputs. A second append therefore replaces the first batch.

[`cc` 1.2.56's `Build::assemble`](https://github.com/rust-lang/cc-rs/blob/cc-v1.2.56/src/lib.rs)
creates native archives in batches of 100 objects. A 101-object library exposes
the defect: the final archive contains only object 101. An iOS simulator link
against the first and final C functions fails for the wrapped archiver and passes
with LLVM's `llvm-ar`, with the same compiler, SDK, target and source inputs.

This fixture isolates the archive boundary seen when an AWS-LC build produces
an archive containing only its final assembly batch, leaving its C API undefined.
It does not alter cryptographic source, bindings, prefixes, or capabilities.

## Run

On macOS with Xcode, Cargo, Rust, and its LLVM tools component:

```sh
rustup component add llvm-tools-preview
python3 apple-archive-append/verify.py
```

Alternatively supply `--llvm-ar /absolute/path/to/llvm-ar` (or `LLVM_AR`).
The script downloads checksum-pinned public upstream wrapper source, compiles it,
and invokes the real pinned `cc` crate through a Cargo build script. It verifies
archive members, C symbol definitions, and final iOS simulator link outcomes.
No simulator execution is required.

On Linux, the wrapper's command translation can be verified separately:

```sh
python3 apple-archive-append/verify.py --command-only
```

The compiled upstream wrapper's `__LIBTOOL_LOG_ONLY` mode exposes the exact
`libtool` invocation. An existing archive occurs only as the output, proving
that its previous contents are not supplied to the replacement command.

## Sources

- [apple_support 2.10.1 libtool wrapper](https://github.com/bazelbuild/apple_support/blob/2.10.1/crosstool/libtool.cc): `processArCreateArgs` translates the operation; `processArgs` consumes the output archive argument.
- [cc-rs 1.2.56](https://github.com/rust-lang/cc-rs/blob/cc-v1.2.56/src/lib.rs): `assemble` batches 100 inputs; `assemble_progressive` uses `cq` to append each batch.
- [LLVM archive tool](https://llvm.org/docs/CommandGuide/llvm-ar.html): the `q` operation appends objects to an existing archive.

The integration correction supplies a declared LLVM archiver to the native build
script. Merely changing symbol prefixes or re-bundling an already truncated
archive cannot restore the missing C objects.
