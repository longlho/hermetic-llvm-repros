"""Model a configure probe that invokes CC with both CFLAGS and LDFLAGS."""

load("@rules_cc//cc:action_names.bzl", "ACTION_NAMES")
load("@rules_cc//cc:find_cc_toolchain.bzl", "find_cpp_toolchain", "use_cc_toolchain")
load("@rules_cc//cc/common:cc_common.bzl", "cc_common")

def _compiler_probe_impl(ctx):
    toolchain = find_cpp_toolchain(ctx)
    features = cc_common.configure_features(
        ctx = ctx,
        cc_toolchain = toolchain,
        requested_features = ctx.features,
        unsupported_features = ctx.disabled_features,
    )
    compile_variables = cc_common.create_compile_variables(
        feature_configuration = features,
        cc_toolchain = toolchain,
    )
    cflags = cc_common.get_memory_inefficient_command_line(
        feature_configuration = features,
        action_name = ACTION_NAMES.c_compile,
        variables = compile_variables,
    )
    out = ctx.actions.declare_file(ctx.label.name + (".exe" if ctx.attr.link else ".o"))
    flags = list(cflags)
    if ctx.attr.link:
        link_variables = cc_common.create_link_variables(
            feature_configuration = features,
            cc_toolchain = toolchain,
            is_linking_dynamic_library = False,
        )
        flags += cc_common.get_memory_inefficient_command_line(
            feature_configuration = features,
            action_name = ACTION_NAMES.cpp_link_executable,
            variables = link_variables,
        )
    else:
        flags += ["-c"]
    ctx.actions.run(
        executable = cc_common.get_tool_for_action(
            feature_configuration = features,
            action_name = ACTION_NAMES.c_compile,
        ),
        arguments = flags + [ctx.file.src.path, "-o", out.path],
        inputs = depset([ctx.file.src], transitive = [toolchain.all_files]),
        outputs = [out],
        mnemonic = "ConfigureCompilerProbe",
    )
    return [DefaultInfo(files = depset([out]))]

compiler_probe = rule(
    implementation = _compiler_probe_impl,
    attrs = {
        "src": attr.label(allow_single_file = [".c"], mandatory = True),
        "link": attr.bool(default = False),
    },
    fragments = ["cpp"],
    toolchains = use_cc_toolchain(),
)
