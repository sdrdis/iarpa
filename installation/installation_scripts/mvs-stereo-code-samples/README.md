# Sample code for EOPCC Validation
## Dependencies
 * liblas (http://www.liblas.org/) - For las file reading and writing, should be linked with GDAL for geospatial tag output.
 * laszip (http://www.laszip.org/) - Linked into liblas for laz file reading and writing (When correctly linked liblas will read or write .laz files based on the file extension).
 * GDAL (http://www.gdal.org/) - For image reading and writing.
 
## Example Usage
Cropping image based on KML reference:
 * write out as tif (note 11 bit per sample output)
                ```path_to_exe/crop-image -k  Challenge1.kml -o challenge1_1.tif input_challenge_1.NTF```
 * write out as jpg (8 bit per sample output)
                ```path_to_exe/crop-image -k  Challenge1.kml -o challenge1_1.jpg input_challenge_1.NTF```
 * Example compression from 11 bits per sample to 8bits output:
                ```input_tif_8bit=255*(((float)input_tif_12bit-min)/(MAX-min)). WITH min=0.0f;MAX=2047.0f;)```
                
Sample laz files for a challenge area can be generated with:
```
./src/las-generator -k Challenge1.kml -o challenge1_example.laz
./src/las-generator -k Challenge2a.kml -o challenge2a_example.laz
```

Laz files can be validated with:
```./src/las-validator challenge1_example.laz -k Challenge1.kml```

## RPC camera model

 In the sample code there is an example on how to extract RPC parameters using GDAL library. GDALRPCInfo data type stores RPC camera info.
 What is needed are the 80 coefficients (```sRPC.adfLINE_NUM_COEFF[0...19],sRPC.adfLINE_DEN_COEFF[0...19],sRPC.adfSAMP_NUM_COEFF[0...19],sRPC.adfSAMP_DEN_COEFF[0...19]```), and scale and offset parameters for each coordinate element 
 (total of 10 additional parameters). E.g. scale and offset for lattitude are sRPC.dfLAT_SCALE,sRPC.dfLAT_OFF.
 RPC parameters are used to obtain image coordinates (row,col) or (line,sample) by forward mapping a 3D point (X,Y,Z).
 
 Info on such parameters can be found:
(formatting details [here](ftp://ftp.ecn.purdue.edu/jshan/proceedings/asprs2005/Files/0031.pdf))
 
 
## Further reading
 This is a collection of references to familiarize yourself with the problem and how other folks have tackled the 3D reconstruction of satellite imagery:
 * G. Dial and J. Grodecki,"RPC replacacement camera models", ASPRS 2005.
 * T. Pollard and J. Mundy, "Change Detection in a 3-d World", CVPR 2007.
 * V. Tao and Y. Hu,"3D Reconstruction Methods Based on the Rational Function Model",Phot.Eng. Rem. Sensing 2002.
 * E. Zheng et.al., "Minimal Solvers for 3D Geometry from Satellite Imagery", ICCV 2015.