$ErrorActionPreference = "Stop"

$synthetic = Resolve-Path "$PSScriptRoot\..\data\synthetic" -ErrorAction SilentlyContinue
if ($synthetic) {
  Get-ChildItem $synthetic -Filter *.csv | Remove-Item -Force
}

Write-Host "Generated synthetic CSVs removed."

