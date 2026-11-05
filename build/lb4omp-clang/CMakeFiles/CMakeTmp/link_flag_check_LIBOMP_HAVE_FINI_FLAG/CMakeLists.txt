cmake_minimum_required(VERSION 2.8)
     project(foo C)
     set(CMAKE_SHARED_LINKER_FLAGS "-Wl,-fini=__kmp_internal_end_fini")
     add_library(foo SHARED src_to_link.c)