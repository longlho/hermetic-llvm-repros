load("@rules_go//go:def.bzl", "go_binary")
load("@with_cfg.bzl", "with_cfg")
transitioned_go_binary, _transitioned = with_cfg(go_binary, executable = True).set("platforms", [Label("@llvm//platforms:macos_arm64")]).set("strip", "never").build()
