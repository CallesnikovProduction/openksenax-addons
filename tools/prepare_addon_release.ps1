[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string] $ApkPath,
    [Parameter(Mandatory)]
    [string] $AddonId,
    [Parameter(Mandatory)]
    [string] $DisplayName,
    [Parameter(Mandatory)]
    [string] $ShortDescription,
    [Parameter(Mandatory)]
    [uri] $ApkUrl,
    [Parameter(Mandatory)]
    [uri] $RepositoryUrl,
    [string] $OutputPath,
    [int] $ProtocolVersion = 1,
    [int] $ManagementApiVersion = 1,
    [int] $MinimumHostApi = 1,
    [string[]] $RequiredHostCapabilities = @("model.text-generation")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-AndroidTool {
    param([Parameter(Mandatory)][string] $Name)

    $command = Get-Command $Name -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -eq $command) {
        throw "$Name is not available in PATH"
    }
    return $command.Source
}

function Invoke-CheckedTool {
    param(
        [Parameter(Mandatory)][string] $Tool,
        [Parameter(Mandatory)][string[]] $Arguments
    )

    $output = & $Tool @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "$Tool failed: $($output -join [Environment]::NewLine)"
    }
    return ($output -join [Environment]::NewLine).Trim()
}

$apk = Get-Item -LiteralPath $ApkPath
if ($apk.Extension -ne ".apk" -or $apk.Length -le 0) {
    throw "ApkPath must point to a non-empty .apk file"
}
if ($ApkUrl.Scheme -ne "https" -or $RepositoryUrl.Scheme -ne "https") {
    throw "ApkUrl and RepositoryUrl must use HTTPS"
}

$apkanalyzer = Resolve-AndroidTool "apkanalyzer"
$apksigner = Resolve-AndroidTool "apksigner"
$absoluteApk = $apk.FullName

$packageName = Invoke-CheckedTool $apkanalyzer @(
    "manifest", "application-id", $absoluteApk
)
$versionCodeText = Invoke-CheckedTool $apkanalyzer @(
    "manifest", "version-code", $absoluteApk
)
$versionName = Invoke-CheckedTool $apkanalyzer @(
    "manifest", "version-name", $absoluteApk
)
$minimumSdkText = Invoke-CheckedTool $apkanalyzer @(
    "manifest", "min-sdk", $absoluteApk
)

[long] $versionCode = 0
[int] $minimumSdk = 0
if (
    -not [long]::TryParse($versionCodeText, [ref] $versionCode) -or
    $versionCode -le 0
) {
    throw "Invalid versionCode reported by apkanalyzer: $versionCodeText"
}
if (
    -not [int]::TryParse($minimumSdkText, [ref] $minimumSdk) -or
    $minimumSdk -le 0
) {
    throw "Invalid minSdk reported by apkanalyzer: $minimumSdkText"
}

$signerOutput = Invoke-CheckedTool $apksigner @(
    "verify", "--verbose", "--print-certs", $absoluteApk
)
$signerMatch = [regex]::Match(
    $signerOutput,
    "Signer #1 certificate SHA-256 digest:\s*([0-9A-Fa-f:]{64,})"
)
if (-not $signerMatch.Success) {
    throw "Cannot find signer SHA-256 in apksigner output"
}

$entry = [ordered]@{
    addonId = $AddonId
    packageName = $packageName
    displayName = $DisplayName
    shortDescription = $ShortDescription
    fullDescription = $null
    executionModel = "AUTONOMOUS_APPLICATION"
    release = [ordered]@{
        versionCode = $versionCode
        versionName = $versionName
        apkUrl = $ApkUrl.AbsoluteUri
        apkSha256 = (
            Get-FileHash -LiteralPath $absoluteApk -Algorithm SHA256
        ).Hash.ToUpperInvariant()
        sizeBytes = $apk.Length
    }
    compatibility = [ordered]@{
        protocolVersion = $ProtocolVersion
        managementApiVersion = $ManagementApiVersion
        minimumHostApi = $MinimumHostApi
        minimumAndroidSdk = $minimumSdk
    }
    requiredHostCapabilities = $RequiredHostCapabilities
    presentation = [ordered]@{
        iconUrl = $null
        repositoryUrl = $RepositoryUrl.AbsoluteUri
    }
    security = [ordered]@{
        official = $true
        signingCertificateSha256 = (
            $signerMatch.Groups[1].Value -replace ":", ""
        ).ToUpperInvariant()
    }
}

$json = $entry | ConvertTo-Json -Depth 8
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $json
} else {
    $resolvedOutput = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath(
        $OutputPath
    )
    [System.IO.File]::WriteAllText(
        $resolvedOutput,
        $json + [Environment]::NewLine,
        [System.Text.UTF8Encoding]::new($false)
    )
    Write-Host "Release entry written to $resolvedOutput"
}
