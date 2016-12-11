#!/bin/bash

source config.bash

# the mvs-stereo-code-samples folder MUST be unzipped in the WORKING_DIR
#unzip mvs-stereo-code-samples.zip
chmod -R ug+w mvs-stereo-code-samples

# Build package for Solver
# get and unzip the mvs-stereo file
cd mvs-stereo-code-samples
if [ -d build ]
then
	rm -r build
fi
mkdir build
cd build
cmake ..
make -j${MAKE_JOBS}
echo "Executables folder: $(pwd)/src"
echo "List directory content:"
ls -all -1 "$(pwd)/src"
