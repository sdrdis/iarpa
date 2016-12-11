#!/bin/bash

source config.bash

# build and install liblas with laszip
cd ${WORKING_DIR}
wget http://download.osgeo.org/liblas/libLAS-1.8.0.tar.bz2
tar xjvf libLAS-1.8.0.tar.bz2 
cd libLAS-1.8.0
mkdir makefiles
cd makefiles
cmake -G "Unix Makefiles" \
	-DCMAKE_INSTALL_PREFIX:PATH=/usr \
	-DWITH_GDAL=ON \
	-DWITH_GEOTIFF=ON \
	-DWITH_LASZIP=ON \
	-DGEOTIFF_INCLUDE_DIR=/usr/include/geotiff \
	-DGDAL_INCLUDE_DIR=/usr/include/gdal \
	-DLASZIP_INCLUDE_DIR=${WORKING_DIR}/laszip-src-2.2.0/include \
	-DCMAKE_VERBOSE_MAKEFILE=ON \
	-DWITH_STATIC_LASZIP=FALSE \
	-DENABLE_CTEST=ON \
	..
make -j${MAKE_JOBS}
sudo make install
