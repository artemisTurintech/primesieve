ctest --test-dir "$PSScriptRoot\build" -j4 --output-on-failure
if (-not $?) { exit 1 }
