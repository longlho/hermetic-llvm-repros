# Compile-and-link probes lose compiler builtin headers

The unmodified hermetic-llvm **0.8.24** release fails a C compiler probe that
combines toolchain compile flags and executable link flags in one invocation.
The same probe passes on unmodified **0.8.25**. Upgrading removes the need for a
local merged-resource header patch.

```sh
python3 run.py merged-resource-headers --case compile_only
python3 run.py merged-resource-headers --case compile_and_link
python3 run.py merged-resource-headers --case compile_and_link --llvm-version 0.8.25
python3 verify-release.py resource-headers
```

The first command is a successful negative control; the second intentionally
fails with `fatal error: 'stddef.h' file not found`; the third succeeds. The
verification command checks all three exact outcomes and succeeds only when
they match. These results were observed on Linux x86-64 with Bazel 9.2.0.

`probe.bzl` obtains the real C compile and executable link flags through
`cc_common`, then invokes the configured compiler on a synthetic C program
using `stddef.h`. This models configure-style probes that use both CFLAGS and
LDFLAGS in one compiler command; it requires no Rust SDK, AWS-LC, Cargo, private
artifacts, or application configuration. The compile-only control removes the
link flags while retaining the same toolchain, source, and action inputs.

LLVM's compile flags select its original compiler resource directory, while
its link flags select a merged resource directory containing target runtime
libraries. When both are supplied, the later `-resource-dir` wins. In 0.8.24,
the merged tree omits builtin headers because directory symlink roots are
filtered before traversal. This accounts for the difference from the
compile-only control. It is not an unavailable system SDK or a missing action
input: changing only the LLVM release fixes the same sandboxed action.

The [0.8.25 merge rule](https://github.com/hermeticbuild/hermetic-llvm/blob/v0.8.25/toolchain/merged_resource_directory.bzl)
admits the parent and source directory roots in `include_srcs_patterns`,
allowing their intended contents to be traversed. Compare the
[0.8.24 rule](https://github.com/hermeticbuild/hermetic-llvm/blob/v0.8.24/toolchain/merged_resource_directory.bzl).
The release is available directly through the
[Bazel Central Registry](https://registry.bazel.build/modules/llvm/0.8.25).
No custom LLVM patch is necessary or retained for this repro. The probe
compiles and links the output; it does not run the produced executable or
claim validation of other target platforms.
