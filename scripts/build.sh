#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if ! test -d vendor/LB4OMP/.git; then
  git clone https://github.com/unibas-dmi-hpc/LB4OMP.git vendor/LB4OMP
fi
git -C vendor/LB4OMP checkout b9d25eca7265a4b5b3a675a1765d489775847938
if git -C vendor/LB4OMP apply --check ../../patches/lb4omp-clang16.patch; then
  git -C vendor/LB4OMP apply ../../patches/lb4omp-clang16.patch
else
  git -C vendor/LB4OMP apply --reverse --check ../../patches/lb4omp-clang16.patch
fi
cmake -S vendor/LB4OMP -B build/lb4omp-clang \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_C_COMPILER=clang-16 \
  -DCMAKE_CXX_COMPILER=clang++-16 -DOPENMP_ENABLE_LIBOMPTARGET=OFF \
  -DLIBOMP_OMPT_SUPPORT=ON -DLIBOMP_ENABLE_SHARED=ON \
  -DLIBOMP_HAVE___RDTSC=ON -DLIBOMP_HAVE_X86INTRIN_H=ON
cmake --build build/lb4omp-clang -j 4
clang++-16 -O3 -std=c++17 -fopenmp -ffp-contract=off \
  -I build/lb4omp-clang/runtime/src src/experiment.cpp \
  -L build/lb4omp-clang/runtime/src -Wl,-rpath,"$PWD/build/lb4omp-clang/runtime/src" \
  -lomp -o build/experiment
