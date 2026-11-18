# SPDX-License-Identifier: GPL-2.0-or-later
cmake_minimum_required(VERSION 3.16)
project(plasma-tweaks-extract LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Qt6 REQUIRED COMPONENTS Core)

add_executable(plasma-tweaks-extract extract_qml.cpp)
target_link_libraries(plasma-tweaks-extract PRIVATE Qt6::Core)
