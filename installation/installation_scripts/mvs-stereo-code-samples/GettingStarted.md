# Prerequisites

Although these are also available on Linux through the package managers (apt-get, yum), those are often not built with the necessary settings
to support LASzip, JPEG2000, or geotags.

[OSGeo4W](http://trac.osgeo.org/osgeo4w/) provides Windows binaries for this libraries,
but still, some libraries may not be built with the necessary settings. OSGeo4W
can be useful to get a working build environment to build libLAS and GDAL with the
correct settings.

You'll need a C++ compiler (we tested with gcc 4.8 and VS2012) and CMake to
build the samples and their dependencies.

## [GDAL](http://www.gdal.org/)
GDAL is the easier way to read and extract metadata from the provided NITF images.

Before building GDAL, install [openjpeg](https://github.com/uclouvain/openjpeg) to
enable support for the JPEG2000 codec used in the NITF images. If GDAL is built without
JPEG2000 support you will get an error when attempting to open the NITF images with the
sample code.

GDAL provides build instructions for many platforms [here](http://trac.osgeo.org/gdal/wiki/BuildHints). Make sure that GDAL found and has
enabled the openjpeg driver during configuration.

## [LASzip](http://www.laszip.org/)
LASzip is used to compress LAS files to reduce disk and bandwidth usage.

The version available through most package managers is sufficient on Linux .
If you're using Windows, LASzip provides binaries on their webpage or you can build
from source.

## [libLAS](http://www.liblas.org)

libLAS provides a compilation guide [here](http://www.liblas.org/compilation.html).

In the CMake cache editor (run either `make edit_cache` or `cmake-gui` in the build directory) make sure:
  * `WITH_GDAL` is set to `ON`
  * `WITH_GEOTIFF` is set to `ON`
  * `WITH_LASZIP` is set to `ON`

The `WITH_GDAL` and `WITH_GEOTIFF` settings enable geotagging support in libLAS.

If CMake has trouble finding some of the dependencies you can set the
relevant variables (`*_INCLUDE_DIRS` and `*_LIBRARIES`) manually.

# Build Instructions

## Linux
Run the commands below:
```
git clone < Address of public/github repo >
cd eopcc-samples
mkdir build
cd build
cmake ..
make edit_cache  # Fix any missing library issues by modifying the cache
make
```

## Windows

These instructions cover using CMake and Visual Studio to build the samples. Please note, when running the samples on Windows you will need to make
sure that the DLLs of the dependencies are on the PATH.

### Command Line Option
 * Clone the repo using [Git for Windows](https://git-scm.com/download/win)
 * Start a Visual Studio Tools command prompt.
 * Run the commands below:

```
cd <cloned directory>
mkdir build
cd build
cmake .. -G "NMake Makefiles"
nmake edit_cache # Fix paths to dependencies
nmake
```

### GUI Option
  * Clone the repo using [Git for Windows](https://git-scm.com/download/win)
    * Start the CMake GUI from the start menu
    * Select the repo as the source directory and any empty directory as the build directory
    * Click Configure, select your generator (i.e. Visual Studio 11 2012 Win64), press Finish
    * It will probably fail to find the dependencies. If you installed the dependencies to the same directory you can
    set `EXTERNAL_LIBS_ROOT` to that directory to resolve these issues.
    * Press Configure again.
    * Press Generate.
  * Navigate to the build directory you created in the CMake GUI and open `eopcc-samples.sln` with Visual Studio.
  * Build the project in Visual Studio.
