# Project Umbra — cross-compile to Windows x64 with MinGW-w64.
# Uses prebuilt MSYS2 mingw64 libraries staged in a sysroot.
# Usage: -DCMAKE_TOOLCHAIN_FILE=cmake/mingw-w64-toolchain.cmake
#        -DUMBRA_MINGW_SYSROOT=/path/to/mingw-sysroot/mingw64

set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_SYSTEM_PROCESSOR x86_64)

set(TOOLCHAIN_PREFIX x86_64-w64-mingw32)
set(CMAKE_C_COMPILER   ${TOOLCHAIN_PREFIX}-gcc)
set(CMAKE_CXX_COMPILER ${TOOLCHAIN_PREFIX}-g++)
set(CMAKE_RC_COMPILER  ${TOOLCHAIN_PREFIX}-windres)

if(NOT UMBRA_MINGW_SYSROOT)
    set(UMBRA_MINGW_SYSROOT "/home/user/mingw-sysroot/mingw64")
endif()

# search the MSYS2 lib sysroot first, then the compiler's own sysroot
set(CMAKE_FIND_ROOT_PATH ${UMBRA_MINGW_SYSROOT} /usr/${TOOLCHAIN_PREFIX})
set(CMAKE_PREFIX_PATH ${UMBRA_MINGW_SYSROOT})

set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY BOTH)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE BOTH)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE BOTH)

# make the staged headers/libs visible to the raw compiler too
include_directories(SYSTEM ${UMBRA_MINGW_SYSROOT}/include)
link_directories(${UMBRA_MINGW_SYSROOT}/lib)
