cmake_minimum_required(VERSION 2.8 FATAL_ERROR)

project(eopcc-samples CXX)


set(EXTERNAL_LIBS_ROOT "" CACHE PATH "Path to external library folder (Provide for convience on Windows)")

if(NOT WIN32)
set(CMAKE_CXX_FLAGS "-std=c++11 -Wreturn-type" ${CMAKE_CXX_FLAGS})
else()
add_definitions(-DNOMINMAX)
endif()


find_path(libLAS_INCLUDE_FILE NAMES liblas.hpp PATHS /usr/local/include/liblas ${EXTERNAL_LIBS_ROOT}/include/liblas)
get_filename_component(libLAS_INCLUDE_DIRS ${libLAS_INCLUDE_FILE} DIRECTORY)
find_library(libLAS_LIBRARIES NAMES las liblas PATHS ${EXTERNAL_LIBS_ROOT}/lib)

if (EXTERNAL_LIBS_ROOT)
  find_path(GDAL_INCLUDE_DIR NAMES gdal.h PATHS ${EXTERNAL_LIBS_ROOT}/include)
  find_library(GDAL_LIBRARY NAMES gdal_i gdal PATHS ${EXTERNAL_LIBS_ROOT}/lib)
endif()

find_package(GDAL REQUIRED)

set(BOOST_ROOT ${EXTERNAL_LIBS_ROOT})
find_package(Boost REQUIRED) # Required by liblas

link_directories(${Boost_LIBRARY_DIRS})
include_directories(${Boost_INCLUDE_DIRS})


include_directories(${libLAS_INCLUDE_DIRS})
include_directories(${GDAL_INCLUDE_DIR})
include_directories(${GDAL_INCLUDE_DIR})

add_subdirectory(external)
include_directories("./include")
include_directories("./external")


add_subdirectory("./lib")
add_subdirectory("./src")

