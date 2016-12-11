
# Header files are only added to the build for nicer Visual Studio projects...
file(GLOB_RECURSE HEADER_FILES ../include/*.hpp)
add_library(eopcc-lib "las_io.cpp" "utility.cpp" "utm_zone.cpp" "gdal_io.cpp" "cloud.cpp" ${HEADER_FILES})
target_link_libraries(eopcc-lib ${libLAS_LIBRARIES} ${GDAL_LIBRARIES} ${KML_LIBRARIES} tinyxml)

