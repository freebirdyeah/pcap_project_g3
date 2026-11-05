cmake_minimum_required(VERSION 2.8)
     project(foo C)
     set(CMAKE_SHARED_LINKER_FLAGS "-Wl,--version-script=/home/shaan/pcap/vendor/LB4OMP/runtime/src/exports_so.txt")
     add_library(foo SHARED src_to_link.c)