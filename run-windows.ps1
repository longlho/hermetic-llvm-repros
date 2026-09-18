param(
    [ValidateSet('upstream', 'patched')][string]$Variant = 'upstream',
    [string]$Bazel = 'bazel',
    [string]$OutputUserRoot = '',
    [switch]$AcceptMsvcEula,
    [switch]$AnalyzeOnly
)
$ErrorActionPreference = 'Stop'
if (-not $AcceptMsvcEula) { throw 'Review Microsoft runtime/SDK licenses, then pass -AcceptMsvcEula.' }
$work = Join-Path $PSScriptRoot ".work/windows-bootstrap/$Variant"
New-Item -ItemType Directory -Force $work | Out-Null
Copy-Item "$PSScriptRoot/windows-bootstrap/*" $work -Recurse -Force
Copy-Item "$PSScriptRoot/windows-bootstrap/.bazelrc" $work -Force
Copy-Item "$PSScriptRoot/windows-bootstrap/.bazelversion" $work -Force
if ($Variant -eq 'patched') {
    Add-Content (Join-Path $work 'MODULE.bazel') '`nsingle_version_override(module_name = "llvm", patch_strip = 1, patches = ["bootstrap.patch"])'.Replace('`n', "`n")
}
$startup = @('--batch', '--nosystem_rc', '--nohome_rc')
if ($OutputUserRoot) { $startup += "--output_user_root=$OutputUserRoot" }
$arguments = @('build', '//:hello', '--platforms=@llvm//platforms:windows_x86_64_msvc', '--repo_env=BAZEL_MSVC_RUNTIME_VISUAL_STUDIO_EULA=1', '--repo_env=BAZEL_WINDOWS_SDK_EULA=1', '--color=no', '--curses=no')
if ($AnalyzeOnly) { $arguments += '--nobuild' }
$logs = Join-Path $PSScriptRoot "results/windows-bootstrap/$Variant"
New-Item -ItemType Directory -Force $logs | Out-Null
Push-Location $work
try {
    $ErrorActionPreference = 'Continue'
    & $Bazel @startup @arguments 2>&1 | Out-File (Join-Path $logs 'hello.log')
    $result = $LASTEXITCODE
} finally { Pop-Location }
Write-Host "windows-bootstrap/hello [$Variant]: exit $result"
exit $result
