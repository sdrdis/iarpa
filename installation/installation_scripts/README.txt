Example installation scripts for the JHUAPL-Package-for-Solvers package, on Ubuntu 14.04.

Tested on:
- AWS, Ubuntu Server 14.04 LTS (HVM), SSD Volume Type - ami-f95ef58a, c4.xlarge.
- VirtualBox, Xubuntu Desktop 14.04.3 LTS

In the "config.bash" file, you can define:
- the number of jobs used for the "make -j" commands (MAKE_JOBS)
- the working directory where all sources will be downloaded (WORKING_DIR).
The mvs-stereo-code-samples will also be downloaded and unzipped in the WORKING_DIR.

Run scripts part1.bash to part5.bash in order:
- install some necessary dependencies
$ ./part1.bash
- install openjpeg and gdal from source
$ ./part2.bash
- install laszip from source
$./part3.bash
- install liblas from source
$ ./part4.bash
- compile the JHUAPL-Package-for-Solvers sample code
$ ./part5.bash

Many commands require "sudo", hence this disclaimer: The scripts will install packages and program from sources, and potentially damage your system, and are provided without guarantee. Please take any necessary precautions: read the scripts, use a dedicated VM ...
Then if some commands need manual confirmation [Yes/No], if you don't know, you may just answer Yes.

To get a some information on the packages and compilation, please read: 
mvs-stereo-code-samples/GettingStarted.md

When all scripts are done, you could update your PATH, with the new executables folder:
$ source update_path.bash
to call the commands directly:
$ crop-image
$ rpc-print
...


