#!/bin/bash

source config.bash

# build openjpeg
cd ${WORKING_DIR}
wget https://github.com/uclouvain/openjpeg/archive/v2.1.1.tar.gz
tar xvf v2.1.1.tar.gz 
cd openjpeg-2.1.1/
mkdir build
cd build
cmake ..
make -j${MAKE_JOBS}
sudo make install

# build gdal
cd ${WORKING_DIR}
wget http://download.osgeo.org/gdal/2.1.0/gdal-2.1.0.tar.gz
tar xvf gdal-2.1.0.tar.gz 
cd gdal-2.1.0/
./configure
make -j${MAKE_JOBS}
sudo make install

# remove potential duplicate gdal
sudo apt-get --assume-yes remove libgdal1h libgdal-dev
