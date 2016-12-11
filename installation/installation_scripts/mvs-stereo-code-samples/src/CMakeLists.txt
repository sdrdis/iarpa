add_executable(las-validator "validator.cpp")
target_link_libraries(las-validator eopcc-lib)

add_executable(crop-image "crop_nitf.cpp")
target_link_libraries(crop-image eopcc-lib ${GDAL_LIBRARIES})

add_executable(get-crop-area "get_crop_area.cpp")
target_link_libraries(get-crop-area eopcc-lib ${GDAL_LIBRARIES})

add_executable(las-generator "generator.cpp")
target_link_libraries(las-generator eopcc-lib ${GDAL_LIBRARIES})

add_executable(rpc-print "rpc_print.cpp")
target_link_libraries(rpc-print eopcc-lib ${GDAL_LIBRARIES})

