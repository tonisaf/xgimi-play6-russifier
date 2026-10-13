<#
.SYNOPSIS
  Builds the Russian skin for the stock XGIMI settings: skin\build\beam-skin-ru.apk.
.DESCRIPTION
  The skin is a resources-only APK (no code, no components). The firmware's SkinEngine loads the
  APK named by the system property persist.sys.xgimi.themeV2.url and replaces the settings app's
  strings by name. Needs the Android SDK build-tools (aapt2, zipalign, apksigner) and a platform
  android.jar; the signing key is the debug key, because the engine does not check the signature.
#>
param(
    [string]$Sdk = $(if ($env:ANDROID_HOME) { $env:ANDROID_HOME } else { 'C:\android\sdk' }),
    [string]$BuildTools = '34.0.0',
    [string]$Platform = 'android-34'
)
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$bt = Join-Path $Sdk "build-tools\$BuildTools"
$jar = Join-Path $Sdk "platforms\$Platform\android.jar"
$key = Join-Path $env:USERPROFILE '.android\debug.keystore'
foreach ($p in "$bt\aapt2.exe", "$bt\zipalign.exe", "$bt\apksigner.bat", $jar, $key) {
    if (-not (Test-Path $p)) { throw "Not found: $p" }
}

$out = Join-Path $here 'build'
Remove-Item $out -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force "$out\compiled" | Out-Null

& "$bt\aapt2.exe" compile --dir "$here\res" -o "$out\compiled"
if ($LASTEXITCODE) { throw 'aapt2 compile failed' }
$flat = @(Get-ChildItem "$out\compiled" -Filter *.flat | ForEach-Object { $_.FullName })
$link = @('link', '-o', "$out\unsigned.apk", '-I', $jar, '--manifest', "$here\AndroidManifest.xml") + $flat
& "$bt\aapt2.exe" $link
if ($LASTEXITCODE) { throw 'aapt2 link failed' }
& "$bt\zipalign.exe" -f 4 "$out\unsigned.apk" "$out\aligned.apk"
if ($LASTEXITCODE) { throw 'zipalign failed' }
& "$bt\apksigner.bat" sign --ks $key --ks-pass pass:android --key-pass pass:android --out "$out\beam-skin-ru.apk" "$out\aligned.apk"
if ($LASTEXITCODE) { throw 'apksigner failed' }
Remove-Item "$out\unsigned.apk", "$out\aligned.apk", "$out\compiled" -Recurse -Force
Get-Item "$out\beam-skin-ru.apk" | Select-Object Name, Length
