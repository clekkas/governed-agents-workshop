$ErrorActionPreference = "Stop"

python "$PSScriptRoot\..\data\generate_synthetic_healthcare_data.py" --output "$PSScriptRoot\..\data\synthetic"
Write-Host "Synthetic data generated."

