# F411/ST-Link/OpenOCD only. Creates disposable copies strictly inside this repository.
param([Parameter(Mandatory=$true)][string]$Stand)
$ErrorActionPreference = 'Stop'
$repo = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../..'))
$standPath = (Resolve-Path -LiteralPath $Stand).Path
$runRoot = Join-Path $repo ('build/relocation validation/' + [guid]::NewGuid().ToString('N'))
$dependency = Join-Path $runRoot 'module checkout'
$consumer = Join-Path $runRoot 'consumer project'
New-Item -ItemType Directory -Path $dependency, $consumer -Force | Out-Null
# Copy tracked source paths only, excluding caches, local stands and build products.
$tracked = & git -C $repo ls-files hwtest examples/minimal-consumer
if ($LASTEXITCODE -ne 0) { throw 'git ls-files failed' }
foreach ($relative in $tracked) {
    if ($relative.StartsWith('hwtest/')) {
        $destination = Join-Path $dependency $relative
    } else {
        $destination = Join-Path $consumer $relative.Substring('examples/minimal-consumer/'.Length)
    }
    New-Item -ItemType Directory -Path (Split-Path $destination) -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $repo $relative) -Destination $destination
}
$sentinel = Join-Path $dependency 'readonly-sentinel.txt'
[IO.File]::WriteAllText($sentinel, 'must remain unchanged')
$acl = Get-Acl -LiteralPath $dependency
$acl.Sddl | Set-Content -LiteralPath (Join-Path $runRoot 'original-acl.sddl')
$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User
$rule = [Security.AccessControl.FileSystemAccessRule]::new(
    $sid, [Security.AccessControl.FileSystemRights]'Write, Delete, DeleteSubdirectoriesAndFiles',
    [Security.AccessControl.InheritanceFlags]'ContainerInherit, ObjectInherit',
    [Security.AccessControl.PropagationFlags]::None, [Security.AccessControl.AccessControlType]::Deny)
$restricted = Get-Acl -LiteralPath $dependency
$restricted.AddAccessRule($rule)
$result = [ordered]@{ status = 'ERROR'; write_guards = @(); acl_restored = $false }
function Expect-Denied([string]$Label, [scriptblock]$Operation) {
    try { & $Operation } catch {
        if ($_.Exception.GetBaseException() -is [UnauthorizedAccessException]) {
            $result.write_guards += $Label
            return
        }
        throw
    }
    throw "Write restriction was ineffective: $Label"
}
$previousTemp, $previousTmp = $env:TEMP, $env:TMP
$localTemp = Join-Path $runRoot 'temp'
New-Item -ItemType Directory -Path $localTemp -Force | Out-Null
try {
    $env:TEMP = $localTemp
    $env:TMP = $localTemp
    Set-Acl -LiteralPath $dependency -AclObject $restricted
    Expect-Denied 'create file' { [IO.File]::WriteAllText((Join-Path $dependency 'forbidden.txt'), 'x') }
    Expect-Denied 'overwrite file' { [IO.File]::WriteAllText($sentinel, 'x') }
    Expect-Denied 'create directory' { [IO.Directory]::CreateDirectory((Join-Path $dependency 'forbidden')) | Out-Null }
    Expect-Denied 'delete file' { [IO.File]::Delete($sentinel) }
    # Use presets from the relocated consumer; no parent project CMake is involved.
    Push-Location $consumer
    try {
        & cmake --preset debug "-DHWTEST_SOURCE_DIR=$dependency" *> (Join-Path $runRoot 'configure.log')
        if ($LASTEXITCODE -ne 0) { throw 'Configure failed; see configure.log' }
        & cmake --build --preset debug *> (Join-Path $runRoot 'build.log')
        if ($LASTEXITCODE -ne 0) { throw 'Build failed; see build.log' }
        & ctest --preset offline *> (Join-Path $runRoot 'offline.log')
        if ($LASTEXITCODE -ne 0) { throw 'Offline CTest failed; see offline.log' }
    } finally { Pop-Location }
    & python -B (Join-Path $PSScriptRoot 'check_consumer_lifecycle.py') --stand $standPath `
        --consumer-root $consumer --module-root $dependency --ctest *> (Join-Path $runRoot 'lifecycle.log')
    if ($LASTEXITCODE -ne 0) { throw 'Hardware lifecycle failed; see lifecycle.log and restoration results' }
    if ([IO.File]::ReadAllText($sentinel) -ne 'must remain unchanged') { throw 'Sentinel changed' }
    $result.status = 'PASS'
} finally {
    try {
        Set-Acl -LiteralPath $dependency -AclObject $acl
        if ((Get-Acl -LiteralPath $dependency).Sddl -ne $acl.Sddl) { throw 'ACL restore mismatch' }
        $result.acl_restored = $true
    } catch {
        $result.status = 'ERROR'
        throw
    } finally {
        $env:TEMP = $previousTemp
        $env:TMP = $previousTmp
        $result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $runRoot 'summary.json')
        Write-Output "Evidence: $runRoot"
    }
}
$result | ConvertTo-Json -Depth 5
