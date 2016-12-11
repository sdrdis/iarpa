sudo apt-get --assume-yes install python-numpy python-scipy python-matplotlib

sudo apt-get --assume-yes install build-essential
sudo apt-get --assume-yes install cmake git libgtk2.0-dev pkg-config libavcodec-dev libavformat-dev libswscale-dev
sudo apt-get --assume-yes install python-dev python-numpy libtbb2 libtbb-dev libjpeg-dev libpng-dev libtiff-dev libjasper-dev libdc1394-22-dev python-pip

sudo apt-get --assume-yes install git
cd ~
mkdir opencv
cd opencv
git clone https://github.com/Itseez/opencv.git
git clone https://github.com/Itseez/opencv_contrib.git
cd opencv
mkdir build
cd build
cmake -D CMAKE_BUILD_TYPE=RELEASE \
	-D CMAKE_INSTALL_PREFIX=/usr/local \
	-D INSTALL_C_EXAMPLES=ON \
	-D INSTALL_PYTHON_EXAMPLES=ON \
	-D OPENCV_EXTRA_MODULES_PATH=~/opencv/opencv_contrib/modules \
	-D BUILD_EXAMPLES=ON \
	..

cmake -D CMAKE_BUILD_TYPE=RELEASE \
	-D CMAKE_INSTALL_PREFIX=/usr/local \
	-D INSTALL_C_EXAMPLES=ON \
	-D INSTALL_PYTHON_EXAMPLES=ON \
	-D OPENCV_EXTRA_MODULES_PATH=~/opencv/opencv_contrib/modules \
	-D BUILD_EXAMPLES=ON \
	-D WITH_FFMPEG=OFF \
	-D BUILD_SHARED_LIBS=OFF ..

#cmake -D CMAKE_BUILD_TYPE=RELEASE \
#	-D CMAKE_INSTALL_PREFIX=/usr/local \
#	-D INSTALL_C_EXAMPLES=ON \
#	-D INSTALL_PYTHON_EXAMPLES=ON \
#	-D OPENCV_EXTRA_MODULES_PATH=~/opencv/opencv_contrib/modules \
#	-D BUILD_EXAMPLES=ON \
#	-D WITH_QT=ON \
#	-D WITH_OPENGL=ON \
#	-D ENABLE_FAST_MATH=1 \
#	-D CUDA_FAST_MATH=1 \
#	-D WITH_CUBLAS=1 \
#	..
make -j4
sudo make install
sudo ldconfig
sudo ln /dev/null /dev/raw1394

sudo pip install scikit-learn
sudo pip install cython
sudo pip install scikit-image

sudo apt-get --assume-yes install libopenexr-dev
sudo pip install openexr
sudo pip install pyproj
sudo pip install fastkml