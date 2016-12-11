#!/bin/bash

# the mvs-stereo-code-samples folder MUST be already unzipped in the WORKING_DIR
MAKE_JOBS=4
WORKING_DIR=${HOME}/iarpa/src
if [ ! -d "${WORKING_DIR}" ]
then
	mkdir -p "${WORKING_DIR}"
fi
