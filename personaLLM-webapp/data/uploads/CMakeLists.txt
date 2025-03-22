cmake_minimum_required(VERSION 3.27)
project(Linux_file_system C)

set(CMAKE_C_STANDARD 11)

include_directories(.)

add_executable(Linux_file_system
        functii-Arb.c
        linux.c
        structs.h)
