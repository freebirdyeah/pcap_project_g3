#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! test -f build/lb4omp-clang/runtime/src/libomp.so; then
  bash scripts/build.sh
fi
clang++-16 -O3 -std=c++17 -fopenmp -ffp-contract=off \
  -I build/lb4omp-clang/runtime/src tradeoff/src/tradeoff.cpp \
  -L build/lb4omp-clang/runtime/src \
  -Wl,-rpath,"$PWD/build/lb4omp-clang/runtime/src" -lomp -o build/tradeoff
