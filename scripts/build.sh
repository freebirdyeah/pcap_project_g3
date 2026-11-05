#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
: "${LB4OMP_SOURCE:?Set LB4OMP_SOURCE to an LB4OMP source checkout}"
cmake -S "$LB4OMP_SOURCE" -B build/lb4omp-clang \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-16 \
  -DCMAKE_CXX_COMPILER=clang++-16 -DOPENMP_ENABLE_LIBOMPTARGET=OFF \
  -DLIBOMP_OMPT_SUPPORT=ON -DLIBOMP_ENABLE_SHARED=ON \
  -DLIBOMP_HAVE___RDTSC=ON -DLIBOMP_HAVE_X86INTRIN_H=ON
cmake --build build/lb4omp-clang -j 4
clang++-16 -O3 -std=c++17 -fopenmp -ffp-contract=off \
  -I build/lb4omp-clang/runtime/src src/experiment.cpp \
  -L build/lb4omp-clang/runtime/src -Wl,-rpath,"$PWD/build/lb4omp-clang/runtime/src" \
  -lomp -o build/experiment
