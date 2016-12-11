#!/bin/bash

source config.bash

# get and build LASZIP
cd ${WORKING_DIR}
wget https://github.com/LASzip/LASzip/releases/download/v2.2.0/laszip-src-2.2.0.tar.gz
wget https://github.com/LASzip/LASzip/releases/download/v2.2.0/laszip-src-2.2.0.tar.gz.md5
md5sum -c laszip-src-2.2.0.tar.gz.md5 || exit 1
tar xzvf laszip-src-2.2.0.tar.gz 
cd laszip-src-2.2.0/
./configure
make -j${MAKE_JOBS}
sudo make install