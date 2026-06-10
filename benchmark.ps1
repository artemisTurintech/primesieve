& "$PSScriptRoot\build\primesieve.exe" 1e10
if (-not $?) { exit 1 }

python "$PSScriptRoot\run_benchmark.py"
if (-not $?) { exit 1 }
