IARPA Contest Submission
========================

This is my IARPA Contest Submission for the [IARPA Multi-View Stereo 3D Mapping Challenge](https://www.iarpa.gov/challenges/3dchallenge.html).

This submission finished 1st in the Explorer Contest, and 3rd in the Master Contest.

Description
-----------

The objective of this software is to evaluate a 3d map from a set of satellite images.

What must be provided:
* A set of satellite images
* A list of suitable pairs of images
* A KML file

What is generated:
* A TXT File containing 3d point positions
or
* A NPZ (numpy) file containing a height map, color map and confidence metric

Main steps can be called independently allowing maximum customization.

License
-------
This code is under [MIT license](https://github.com/sdrdis/iarpa_contest_submission/blob/master/MIT-LICENSE.txt).

Authors
-------
* [Sebastien Drouyer](http://sebastien.drouyer.com) - alias [@sdrdis](https://twitter.com/sdrdis)

Third party softwares
---------------------

This code relies heavily on the [NASA Ames Stereo Pipeline](https://ti.arc.nasa.gov/tech/asr/intelligent-robotics/ngt/stereo/). It has been directly included in this repository (in the `lib_exec/StereoPipeline` folder) for ease of installation.

It also rely on the sample code provided during the contest that can be found in the `installation/installation_scripts` folder.

How to install
--------------

How to use
----------

Example tutorial
----------------

In-depth Documentation
----------------------