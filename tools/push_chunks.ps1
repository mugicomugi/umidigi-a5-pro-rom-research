<#
.SYNOPSIS
Push a directory of small chunks to a device over adb, with per-file timeout,
retry and resume.

.DESCRIPTION
The unofficial TWRP 3.7.0 (Hadenix) build for the UMIDIGI A5 Pro cannot receive
files larger than roughly 1-2 MB over adb: push and sideload stall at ~0%.
Files of 1 MB and below go through. Splitting into 800 KB chunks worked for an
812 MB ROM (992 of 992 chunks) in a fresh TWRP session.

Prefer pushing while Android is booted instead - booted-system adb moved 3 GB
in 90 s on the same cable. Use this only when no bootable system is available.

Split first (Git Bash / Linux):   split -b 800k -d -a 4 rom.zip parts/c_
Reassemble on device afterwards:  adb shell "cat /sdcard/parts/* > /sdcard/rom.zip"
Then compare md5sum on both ends before flashing.

.EXAMPLE
.\push_chunks.ps1 -Adb C:\platform-tools\adb.exe -ChunkDir .\parts -RemoteDir /sdcard/parts
#>
param(
    [Parameter(Mandatory)] [string] $Adb,
    [Parameter(Mandatory)] [string] $ChunkDir,
    [string] $RemoteDir = "/sdcard/parts",
    [string] $DoneLog = (Join-Path $ChunkDir "..\push_done.txt"),
    [int] $TimeoutMs = 15000,
    [int] $Attempts = 3
)

$ErrorActionPreference = "Continue"

function Test-DeviceOnline {
    foreach ($waitMs in 0, 2000, 3000) {
        Start-Sleep -Milliseconds $waitMs
        $state = & $Adb get-state 2>&1
        if ($state -eq "device" -or $state -eq "recovery") { return $true }
    }
    return $false
}

if (-not (Test-Path $DoneLog)) { New-Item -ItemType File -Path $DoneLog | Out-Null }
$done = @(Get-Content $DoneLog -ErrorAction SilentlyContinue)

if (-not (Test-DeviceOnline)) { throw "device is not online - replug the USB cable" }
& $Adb shell "mkdir -p $RemoteDir" | Out-Null

$files = Get-ChildItem -Path $ChunkDir -File | Sort-Object Name
$i = 0
$failed = 0

foreach ($f in $files) {
    $i++
    if ($done -contains $f.Name) { continue }

    $ok = $false
    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        $psi = New-Object System.Diagnostics.ProcessStartInfo
        $psi.FileName = $Adb
        $psi.Arguments = "push `"$($f.FullName)`" `"$RemoteDir/$($f.Name)`""
        $psi.RedirectStandardOutput = $true
        $psi.RedirectStandardError = $true
        $psi.UseShellExecute = $false
        $proc = [System.Diagnostics.Process]::Start($psi)

        if (-not $proc.WaitForExit($TimeoutMs)) {
            try { $proc.Kill() } catch {}
            Write-Host "[$i/$($files.Count)] $($f.Name) timeout (attempt $attempt)"
        } elseif ($proc.ExitCode -eq 0) {
            $ok = $true
            break
        } else {
            Write-Host "[$i/$($files.Count)] $($f.Name) failed (attempt $attempt): $($proc.StandardError.ReadToEnd())"
        }

        # Restarting the adb server does not recover an "offline" TWRP device on this
        # hardware - only a physical replug does - so stop instead of burning retries.
        if (-not (Test-DeviceOnline)) {
            Write-Host "device went offline at $($f.Name); replug the cable and rerun (progress is kept in $DoneLog)"
            exit 1
        }
    }

    if ($ok) {
        Add-Content -Path $DoneLog -Value $f.Name
        if ($i % 25 -eq 0) { Write-Host "[$i/$($files.Count)] ok" }
    } else {
        $failed++
    }
}

Write-Host "done: $($files.Count) chunks, $failed failed"
if ($failed -gt 0) { exit 1 }
