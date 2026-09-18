def _symbols_impl(ctx):
    output = ctx.actions.declare_file(ctx.label.name + ".txt")
    ctx.actions.run_shell(
        command = '"$1" --defined-only --format=posix "$2" > "$3" && grep -q repro_exported_symbol "$3"',
        arguments = [ctx.executable.nm.path, ctx.files.object[0].path, output.path],
        tools = [ctx.attr.nm[DefaultInfo].files_to_run],
        inputs = ctx.files.object,
        outputs = [output],
    )
    return [DefaultInfo(files = depset([output]))]
symbols = rule(implementation = _symbols_impl, attrs = {
    "object": attr.label(mandatory = True),
    "nm": attr.label(mandatory = True, executable = True, allow_single_file = True, cfg = "exec"),
})
