# Results

Validation in progress. Host: macOS ARM64. Bazel: 9.2.0. hermetic-llvm: 0.8.21. No user/system Bazel configuration.

- Public `@llvm//tools:llvm-nm`: **passes**, extracts the synthetic exported symbol. A new custom alias is not yet justified.
- Go platform transition: **passes** without patch. Further exec-transition checks are separate.
- MSVC `_I64_MAX`: **fails** without patch: `use of undeclared identifier '_I64_MAX'`.
- Host macOS bindgen: **passes** without patch. Cross-target check is separate.

No conclusion is based solely on an expected nonzero exit. Missing tools, downloads, and unrelated setup failures are not counted as defect reproductions.
