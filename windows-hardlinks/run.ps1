param([switch]$Container)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$work = Join-Path $root '.work/hardlinks'
New-Item -ItemType Directory -Force $work | Out-Null
$image = 'mcr.microsoft.com/windows/servercore:ltsc2022'
if ($Container) {
    docker pull $image
    if ($LASTEXITCODE) { throw 'Cannot pull Windows container image' }
}

foreach ($variant in @('upstream', 'patched')) {
    $workspace = Join-Path $work $variant
    New-Item -ItemType Directory -Force $workspace | Out-Null
    Copy-Item "$PSScriptRoot/MODULE.bazel", "$PSScriptRoot/BUILD.bazel", "$PSScriptRoot/hardlinks.patch" $workspace
    if ($variant -eq 'patched') {
        Add-Content "$workspace/MODULE.bazel" 'single_version_override(module_name = "llvm", patch_strip = 1, patches = ["//:hardlinks.patch"])'
    }
    Push-Location $workspace
    try {
        bazel --batch --windows_enable_symlinks --nosystem_rc --nohome_rc fetch '--repo=@llvm-toolchain-minimal-windows-amd64'
        if ($LASTEXITCODE) { throw "Bazel fetch failed: $variant" }
        $outputBase = (bazel --batch --windows_enable_symlinks --nosystem_rc --nohome_rc info output_base | Select-Object -Last 1).Trim()
        if ($LASTEXITCODE) { throw 'Cannot find Bazel output base' }
        $repos = @(Get-ChildItem "$outputBase/external" -Directory | Where-Object { $_.Name.EndsWith('+llvm-toolchain-minimal-windows-amd64') })
        if ($repos.Count -ne 1) { throw "Expected one archive repository, got $($repos.Count)" }
        $repo = $repos[0].FullName
        $clang = Join-Path $repo 'bin/clang-cl.exe'
        $linker = Join-Path $repo 'bin/lld-link.exe'
        $links = @(Get-ChildItem "$repo/bin" -File -Force | Where-Object LinkType -eq SymbolicLink)
        if ($variant -eq 'upstream') {
            if ($links.Count -eq 0 -or (Get-Item $clang).LinkType -ne 'SymbolicLink') { throw 'Baseline did not retain archive symlinks' }
        } else {
            if ($links.Count -ne 0) { throw 'Patched repository still contains symlinks' }
            foreach ($tool in @($clang, $linker)) {
                if ((Get-Item $tool).LinkType -ne 'HardLink') { throw "Not a hardlink: $tool" }
                $siblings = fsutil hardlink list $tool
                if ($LASTEXITCODE -or -not ($siblings -match '\\bin\\llvm.exe$')) { throw 'Tool does not share llvm.exe file identity' }
            }
        }
        & $clang --version
        if ($LASTEXITCODE) { throw 'Host compiler launch failed' }
        & $linker --version
        if ($LASTEXITCODE) { throw 'Host linker launch failed' }
        Set-Content "$workspace/probe.c" 'int answer(void) { return 42; }'
        & $clang /nologo /c "$workspace/probe.c" "/Fo$workspace/probe.obj"
        if ($LASTEXITCODE -or -not (Test-Path "$workspace/probe.obj")) { throw 'Host compilation failed' }
        if ($Container) {
            # Same mounted repository and native process API for both variants.
            $probe = @'
$ErrorActionPreference = 'Stop'
try {
    $p = New-Object System.Diagnostics.Process
    $p.StartInfo.FileName = 'C:\fixture\bin\clang-cl.exe'
    $p.StartInfo.Arguments = '--version'
    $p.StartInfo.UseShellExecute = $false
    [void]$p.Start()
    $p.WaitForExit()
    exit $p.ExitCode
} catch {
    $e = $_.Exception
    while ($e.InnerException) { $e = $e.InnerException }
    if ($e -is [ComponentModel.Win32Exception] -and $e.NativeErrorCode -eq 3) {
        Write-Output 'CreateProcessW: ERROR_PATH_NOT_FOUND (3)'
        exit 33
    }
    throw
}
'@
            $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($probe))
            docker run --rm --isolation=process --mount "type=bind,source=$repo,target=C:\fixture,readonly" $image powershell.exe -NoProfile -EncodedCommand $encoded
            $result = $LASTEXITCODE
            $expected = if ($variant -eq 'upstream') { 33 } else { 0 }
            if ($result -ne $expected) { throw "Container $variant returned $result; expected $expected" }
        }
        Write-Output "PASS: $variant archive layout, host launch, compile; container=$Container"
    } finally { Pop-Location }
}
