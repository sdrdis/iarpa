#!/bin/bash

source config.bash

cd ${WORKING_DIR}

# install some required packages
sudo apt-get --assume-yes update
sudo apt-get --assume-yes install gcc g++ unzip dpkg-dev cmake geotiff-bin libgeotiff-dev libboost-all-dev
sudo apt-get --assume-yes build-dep liblas-bin gdal-bin
