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

Requirements
------------

This code has been tested on Ubuntu 14.04 LTS. It probably works on Linux and Unix operating system. It *might* work on Windows, with some changes: replacing the StereoPipeline folder, changing the installation script...

How to install
--------------

First, get this software by cloning on github:

```
sudo apt-get install git
git clone https://github.com/sdrdis/iarpa_contest_submission.git
```

*Or* downloading the zip file and unzipping it:

```
sudo apt-get install unzip
wget https://github.com/sdrdis/iarpa_contest_submission/archive/master.zip
unzip master.zip
```

Then go inside the main folder and launch:

```
sudo ./install.sh
```

It will install OpenCV and GDAL notably, so it might take some time...

How to use
----------

We kept the same convention than during the contest, the software runs like this:

```
python chain.py [Input KML file] [Path to NITF image folder] [Output file]
```

The first argument is the location of the KML file indicating which area to reconstruct in 3D. The second argument is
the location of the folder containing all NITF images (with a NTF extension). The third argument is the output file
(extension can either be *.txt or *.npz).

The utility can be broken into two smaller utilities:

The first utility proceeds each pair and generates a 3d map for each of them:

```
python chain_pairwise_pc.py [Input KML file] [Path to NITF image folder]
```

The second utility merge all the 3d maps into a single one:

```
python chain_merge_pcs.py [Input KML file] [Output file]
```

That means that you can customize the stereo algorithm for each pair, and then still merge them using our software
with the `chain_merge_pcs.py`.

Parameters can be customized in the `params.py` file. Each parameter has been commented so take a look at the file.

Example tutorial
----------------

In-depth Documentation
----------------------

Possible improvements
---------------------