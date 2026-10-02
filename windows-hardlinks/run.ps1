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

function Test-ContainerLaunch($Source, $Destination, $Expected) {
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
    $probe = $probe.Replace('C:\fixture', $Destination)
    $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($probe))
    docker run --rm --isolation=process --mount "type=bind,source=$Source,target=$Destination,readonly" $image powershell.exe -NoProfile -EncodedCommand $encoded
    if ($LASTEXITCODE -ne $Expected) { throw "Container returned $LASTEXITCODE; expected $Expected" }
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
        # Bazel 9 external entries may be junctions into its repository cache.
        if ($repos[0].LinkType) {
            $target = @($repos[0].Target)[0]
            $repo = if ([IO.Path]::IsPathRooted($target)) { $target } else { [IO.Path]::GetFullPath((Join-Path $repos[0].Parent.FullName $target)) }
        }
        $repo = $repo -replace '^\\\\\?\\', ''
        $clang = Join-Path $repo 'bin/clang-cl.exe'
        $linker = Join-Path $repo 'bin/lld-link.exe'
        Get-Item $clang | Select-Object FullName, LinkType, Target | Format-List
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
            # Preserve absolute link targets: relocation is a different failure.
            Test-ContainerLaunch $repo $repo 0
        }
        Write-Output "PASS: $variant archive layout, host launch, compile; container=$Container"
    } finally { Pop-Location }
}

# Isolate relative-link failure from Bazel's absolute-link extraction behavior.
$relative = Join-Path $work 'relative fixture'
New-Item -ItemType Directory -Force "$relative/bin" | Out-Null
Copy-Item "$repo/bin/llvm.exe" "$relative/bin/llvm.exe"
Push-Location "$relative/bin"
try {
    cmd /c 'mklink clang-cl.exe llvm.exe'
    if ($LASTEXITCODE) { throw 'Cannot create relative symlink' }
} finally { Pop-Location }
if ([IO.Path]::IsPathRooted(@((Get-Item "$relative/bin/clang-cl.exe").Target)[0])) { throw 'Fixture link must be relative' }
& "$relative/bin/clang-cl.exe" --version
if ($LASTEXITCODE) { throw 'Relative symlink must work on host' }
if ($Container) { Test-ContainerLaunch $relative 'C:\fixture' 33 }

# Read exact command from candidate patch; no duplicate implementation.
$commandLines = Get-Content "$PSScriptRoot/hardlinks.patch" | Where-Object { $_ -match '^\+    "' }
$command = ($commandLines | ForEach-Object { $_.Substring(1).Trim().TrimEnd(',') | ConvertFrom-Json }) -join ' '
$previousDirectory = [Environment]::CurrentDirectory
try {
    [Environment]::CurrentDirectory = $relative
    Set-Location $env:TEMP  # Simulate a PowerShell profile changing location.
    Invoke-Expression $command
    if ((Get-Item "$relative/bin/clang-cl.exe").LinkType -ne 'HardLink') { throw 'Relative fixture was not relinked' }
    Invoke-Expression $command  # Conversion must be idempotent.
} finally {
    [Environment]::CurrentDirectory = $previousDirectory
    Set-Location $root
}
& "$relative/bin/clang-cl.exe" --version
if ($LASTEXITCODE) { throw 'Relinked fixture must work on host' }
if ($Container) { Test-ContainerLaunch $relative 'C:\fixture' 0 }
Write-Output 'PASS: relative symlink negative control, hardlink fix, changed PowerShell location, idempotence'
