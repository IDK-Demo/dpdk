import os
import shutil
def configure(bundle):
    os.system(
        f"cd {bundle.get_default_project().get_path()} && meson setup {bundle.get_build_dir()} --prefix=/ --libdir=lib "
        "--default-library=static -Denable_kmods=true -Ddisable_libs=flow_classify -Ddisable_drivers=crypto/openssl")

    return 0


def build(bundle):
    install_dir = bundle.get_build_dir() / "install_dir"
    command = f"DESTDIR={install_dir} ninja -C {bundle.get_build_dir()} install"
    print(f"Running command: {command}")
    code = os.system(command) >> 8
    print(f"Build completed with code: {code}")
    return code

def get_build_dir(bundle):
    return bundle.get_build_dir() / "install_dir"

def get_artefacts_cmake_file(bundle):
    return """cmake_minimum_required(VERSION 3.26)
project(dpdk LANGUAGES CXX)

add_library(dpdk_dpdk INTERFACE)
add_library(dpdk::dpdk ALIAS dpdk_dpdk)

target_include_directories(dpdk_dpdk INTERFACE ${CMAKE_CURRENT_SOURCE_DIR}/include)

find_package(PkgConfig REQUIRED)
set(ENV{PKG_CONFIG_PATH} "${CMAKE_CURRENT_SOURCE_DIR}/lib/pkgconfig")
execute_process(
        COMMAND pkg-config --static --libs libdpdk
        OUTPUT_VARIABLE DPDK_STATIC_LIBS
        OUTPUT_STRIP_TRAILING_WHITESPACE
)
message(STATUS "DPDK_LIBRARIES: ${DPDK_STATIC_LIBS}")

target_link_directories(dpdk_dpdk INTERFACE ${CMAKE_CURRENT_SOURCE_DIR}/lib)
target_link_libraries(dpdk_dpdk INTERFACE ${DPDK_STATIC_LIBS} numa)
"""

def copy_artefacts(bundle, artefacts_repo_dir):
    build_dir = get_build_dir(bundle)
    shutil.copytree(build_dir / "include", artefacts_repo_dir / "include")
    shutil.copytree(build_dir / "bin", artefacts_repo_dir / "bin")
    lib_dir = artefacts_repo_dir / "lib"
    lib_dir.mkdir(parents=True, exist_ok=True)
    for file in (build_dir / "lib").rglob("*.a"):
        target_path = lib_dir / file.relative_to(build_dir / "lib")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(file, target_path)
    for file in (build_dir / "lib").rglob("*.pc"):
        target_path = lib_dir / file.relative_to(build_dir / "lib")
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(file, lib_dir / file.relative_to(build_dir / "lib"))