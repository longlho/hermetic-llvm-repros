# Bindgen recursively infers an abstract union template's layout

A ten-line synthetic recursive union template panics in unmodified bindgen
**0.72.1** and **0.73.2**:

```text
Not an item: ItemId(...)
```

This fixture has no SDK, WebRTC, C++ standard-library header, system SDK,
private package, or configured hermetic-llvm toolchain dependency. It needs Cargo/Rust 1.92+,
Python 3.10+, `patch`, and libclang. Set `LIBCLANG_PATH` if clang-sys cannot
find the installed shared library.

```sh
python3 bindgen-recursive-union/verify.py
python3 bindgen-recursive-union/verify.py --version 0.72.1
```

The verification script downloads checksum-pinned public crate sources into
ignored `.work/`, then compares unmodified and candidate sources with the same
manifest, synthetic header, host target, and libclang. It expects exactly the
upstream `Not an item` panic and candidate success for both releases: four
checks total. Candidate success also asserts that bindings for the union were
generated. Raw local diagnostics remain under ignored `results/`.

The candidate adds a four-line guard to `CompInfo::layout`: an abstract
template has no concrete layout until instantiation, so bindgen returns
`None` when clang supplies no layout. Its fallback otherwise follows the
recursive union member back to the union currently loaned out of the IR.
Moving the layout computation outside the loan would leave recursive inference
rather than establish a concrete template size. Layouts already supplied by
clang, including concrete template instantiations, continue to use that layout.

Observed on Linux x86-64 with libclang 22.1.8. The original consuming case is
LLVM 23 libc++'s recursive `__union` template in `aligned_union.h`, reached by
WebRTC APM headers during Windows GNU cross-binding generation. The synthetic
fixture removes every one of those dependencies and reproduces on the host
target. Marking or blocklisting `std::.*` opaque does not bypass the failing
layout pass in that consuming case.

Primary source:
[bindgen 0.72.1 union layout fallback](https://github.com/rust-lang/rust-bindgen/blob/v0.72.1/bindgen/ir/comp.rs),
[bindgen 0.73.2 layout pass](https://github.com/rust-lang/rust-bindgen/blob/v0.73.2/bindgen/ir/context.rs),
[LLVM aligned union template](https://github.com/llvm/llvm-project/blob/main/libcxx/include/__type_traits/aligned_union.h).
This establishes a bindgen defect; it does not attribute it to hermetic-llvm.
