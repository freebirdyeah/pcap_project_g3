cmake_minimum_required(VERSION 2.8)
     project(foo C)
     set(CMAKE_SHARED_LINKER_FLAGS "-Wl,-x")
     add_library(foo SHARED src_to_link.c)