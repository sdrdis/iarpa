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

How it does it:
* First, it calculates a 3D map for each defined pair of images.
* Then, it merge all the 3D map into a single one.

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

First, get this software by cloning it on github:

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
(extension can either be `*.txt` or `*.npz`).

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

There exists also, for the user convenience, a vizualization utility for `*.npz` results:

```
python vizualize_result.py [NPZ file] [Output folder]
```

This vizualization file creates three image files with self-explanatory names:
* `height_map.png`
* `color_map.png`
* `confidence.png`

Example tutorial
----------------

We will rely on the contest data to show how the utility can be used and how `params.py` should be modified.

First, we will download only a small part of the images set as you would need more than 30 GB of storage. The following
will only need about 4.5 GB of storage. From the main folder, launch:

```
mkdir data
cd data
wget http://multiview-stereo.s3.amazonaws.com/18DEC15WV031000015DEC18140455-P1BS-500515572010_01_P001_________AAE_0AAAAABPABJ0.NTF
wget http://multiview-stereo.s3.amazonaws.com/18DEC15WV031000015DEC18140510-P1BS-500515572040_01_P001_________AAE_0AAAAABPABJ0.NTF
wget http://multiview-stereo.s3.amazonaws.com/18DEC15WV031000015DEC18140522-P1BS-500515572020_01_P001_________AAE_0AAAAABPABJ0.NTF
wget http://multiview-stereo.s3.amazonaws.com/18DEC15WV031000015DEC18140533-P1BS-500515572050_01_P001_________AAE_0AAAAABPABJ0.NTF
wget http://multiview-stereo.s3.amazonaws.com/18DEC15WV031000015DEC18140544-P1BS-500515572060_01_P001_________AAE_0AAAAABPABJ0.NTF
wget http://multiview-stereo.s3.amazonaws.com/18DEC15WV031000015DEC18140554-P1BS-500515572030_01_P001_________AAE_0AAAAABPABJ0.NTF
```

We also need a KML file. We will take the one of the explorer contest. From the main folder, launch:

```
mkdir kml
cd kml
wget http://www.topcoder.com/contest/problem/MultiViewStereoExplorer/Challenge1.kml
```

Then, go to the main folder. As we only chose a part of the contest images, we need to change the pair filenames.
As a reminder, the software first compute a 3d map for each image pair. This pairwise 3d reconstruction won't work
for all pairs, so the user have to define them. He can do it by changing the `pairs_filenames` variable in the
`params.py` file. Here, replace:

```
pairs_filenames = [
...
]
```
By:

```
pairs_filenames = [
			['18DEC15WV031000015DEC18140455-P1BS-500515572010_01_P001_________AAE_0AAAAABPABJ0.NTF',
			 '18DEC15WV031000015DEC18140533-P1BS-500515572050_01_P001_________AAE_0AAAAABPABJ0.NTF'], #1-4
			 
			['18DEC15WV031000015DEC18140510-P1BS-500515572040_01_P001_________AAE_0AAAAABPABJ0.NTF',
			 '18DEC15WV031000015DEC18140544-P1BS-500515572060_01_P001_________AAE_0AAAAABPABJ0.NTF'], #2-5
			 
			['18DEC15WV031000015DEC18140522-P1BS-500515572020_01_P001_________AAE_0AAAAABPABJ0.NTF',
			 '18DEC15WV031000015DEC18140554-P1BS-500515572030_01_P001_________AAE_0AAAAABPABJ0.NTF'], #3-6
]
```

The image we chose are a sequence taken at approximately the same time with slightly different angles.
We chose pairs with a sufficient baseline but not too much changes.


In the main folder, create the `out` folder where we will save our result:

```
mkdir out
```

Everything should be ready, you can launch the software:

```
python chain.py kml/Challenge1.kml data/ out/test.npz
```

Once the software has finished running, you can vizualize the result like that:

```
python vizualize_result.py out/test.npz out/
```

It will create 3 files, with self-explanatory names:
* `height_map.png`
* `color_map.png`
* `confidence.png`

TODO: Images

As you can see, there are a lot of undefined areas (depicted in gray). These areas are low confidence values that
are by default removed. You can change this behavior by changing the `relative_consensus` parameter in the `params.py` file. You can also
remove all post-processing (including the removal of low confidence values) by setting `height_map_post_process_enabled` to `false`.

Once this is done, you can execute only the second step of our algorithm, since changing this parameter didn't change
the way pair-wise stereo reconstruction was done.

```
python chain_merge_pcs.py kml/Challenge1.kml out/test_2.npz
```

In-depth Documentation
----------------------

Possible improvements
---------------------