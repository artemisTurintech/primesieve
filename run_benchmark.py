#!/usr/bin/env python3
"""
Benchmark libprimesieve: count all primes in [2, SIEVE_LIMIT].

One unit of work = one call to primesieve_count_primes(2, SIEVE_LIMIT).

Metrics reported:
  ms_per_call    – wall-clock milliseconds per count operation (latency)
  primes_per_sec – primes counted per second (throughput)
"""

import ctypes
import json
import math
import os
import timeit

# ── configuration ──────────────────────────────────────────────────────────────
NUMBER      = 5           # calls per trial  (timeit `number`)
REPEAT      = 7           # number of trials (timeit `repeat`)
SIEVE_LIMIT = 10**9       # count primes in [2, SIEVE_LIMIT]
DLL_PATH    = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "build", "libprimesieve.dll")
# ───────────────────────────────────────────────────────────────────────────────


def _load_lib(path: str):
    # Python 3.8+: add the DLL's directory so Windows can resolve its dependencies
    os.add_dll_directory(os.path.dirname(os.path.abspath(path)))
    lib = ctypes.CDLL(path)
    lib.primesieve_count_primes.restype  = ctypes.c_uint64
    lib.primesieve_count_primes.argtypes = [ctypes.c_uint64, ctypes.c_uint64]
    lib.primesieve_version.restype       = ctypes.c_char_p
    return lib


def _mean(xs):
    return sum(xs) / len(xs)


def _stdev(xs, m=None):
    m = m if m is not None else _mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))


def main():
    if not os.path.exists(DLL_PATH):
        raise FileNotFoundError(
            f"DLL not found at {DLL_PATH!r}.\n"
            "Build the project first:\n"
            "  cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release\n"
            "  cmake --build build --parallel"
        )

    lib     = _load_lib(DLL_PATH)
    version = lib.primesieve_version().decode()

    # warm-up: one call to exclude cold-start / cache-fill cost from timing
    prime_count = int(lib.primesieve_count_primes(2, SIEVE_LIMIT))

    # time NUMBER calls per trial, REPEAT trials
    # each returned value is total wall-clock seconds for NUMBER calls
    trial_totals = timeit.repeat(
        stmt="lib.primesieve_count_primes(2, SIEVE_LIMIT)",
        globals={"lib": lib, "SIEVE_LIMIT": SIEVE_LIMIT},
        number=NUMBER,
        repeat=REPEAT,
    )

    per_call_s = [t / NUMBER for t in trial_totals]
    mean_s     = _mean(per_call_s)
    std_s      = _stdev(per_call_s, mean_s)

    # throughput: error propagated via d(C/μ)/dμ = -C/μ² → σ_T = T*(σ/μ)
    throughput_mean = prime_count / mean_s
    throughput_std  = throughput_mean * (std_s / mean_s)

    # one row per trial; each row is one independent measurement
    rows = [
        {
            "number":         NUMBER,
            "repeat":         REPEAT,
            "sieve_limit":    SIEVE_LIMIT,
            "ms_per_call":    round(s * 1e3, 4),
            "primes_per_sec": round(prime_count / s),
        }
        for s in per_call_s
    ]

    print(json.dumps(rows, indent=2))
    print(f"\nSummary ({REPEAT} trials, {NUMBER} calls each):")
    print(f"  ms_per_call    {round(mean_s * 1e3, 4)} ± {round(std_s * 1e3, 4)} ms")
    print(f"  primes_per_sec {round(throughput_mean):,} ± {round(throughput_std):,}")

    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "artemis_results.json")
    with open(out_path, "w") as f:
        json.dump(rows, f, indent=2)

    print(f"\nResults written to {out_path}")


if __name__ == "__main__":
    main()
