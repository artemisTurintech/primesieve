$env:CC  = "gcc"
$env:CXX = "g++"

cmake -S "$PSScriptRoot" -B "$PSScriptRoot\build" -G Ninja -DBUILD_TESTS=ON -DCMAKE_BUILD_TYPE=Release
if (-not $?) { exit 1 }

cmake --build "$PSScriptRoot\build" --parallel
if (-not $?) { exit 1 }
