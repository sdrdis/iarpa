#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>

#include <gdal.h>
#include <gdal_priv.h>
#include <gdal_alg.h>

#include <ogr_spatialref.h>

#include <tclap/CmdLine.h>

#include <eopcc/utility.hpp>
#include <eopcc/las_io.hpp>
#include <eopcc/gdal_io.hpp>

// VS2012 doesn't have round 
#ifdef WIN32
	int round(double val) {
		return (val < 0) ? ceil(val - 0.5) : floor(val + 0.5);
	}
#else 
	using std::round;
#endif

bool replace(std::string& str, const std::string& from, const std::string& to) {
    size_t start_pos = str.find(from);
    if(start_pos == std::string::npos)
        return false;
    str.replace(start_pos, from.length(), to);
    return true;
}

// Fills the intensity of a point cloud using the given image and GDAL (void*) transformer
bool FillIntensityFromImage(eopcc::PointCloud& point_cloud, eopcc::ImageType& img, const eopcc::CropInfo& crop_info, void* transformer,
							double min_intensity, double intensity_scale) {
	OGRSpatialReference pj_utm, pj_latlong;
	pj_latlong.importFromProj4("+proj=latlong +datum=WGS84");
	pj_utm.importFromProj4(point_cloud.spatial_ref.GetProj4().c_str());
	
	OGRCoordinateTransformation* coordinate_transform;
	coordinate_transform = OGRCreateCoordinateTransformation(&pj_utm, &pj_latlong);


 	for (size_t i=0; i < point_cloud.size(); ++i) {
 		double lon = point_cloud.loc[i].x;
 		double lat = point_cloud.loc[i].y;
 		double z = point_cloud.loc[i].z;

 		coordinate_transform->Transform(1, &lon, &lat);

		double pixel_i, pixel_j;
		pixel_i = lon;
		pixel_j = lat;
		int success;
		GDALRPCTransform(transformer, true, 1, &pixel_i, &pixel_j, &z, &success);
		if (!success)
			continue;

		int ii, jj;

		ii = round(pixel_i) - crop_info.pixel_begin;
		jj = round(pixel_j) - crop_info.line_begin;


		//std::cout << point_cloud.loc[i] - point_cloud.extent.min_corner() << ": " << ii << ", " << jj << std::endl;

		if (ii < 0 || jj < 0)
			continue;
		if (ii >= img.width || jj >= img.height) 
			continue;


		double intensity = 0.0;
		for (int ik = 0; ik < img.bands; ik++) {
			int data = img.data[jj*img.width + ii*img.bands+ik];
			intensity = intensity + data;
		}

		intensity = intensity/img.bands;
		intensity = (intensity - min_intensity)*intensity_scale;

		point_cloud.intensity[i] = intensity;
 	}

 	return true;
}

// Example program to demonstrate some very basic things you can do with 
// to work with NITF images with RPC00B metadata 
bool CropImageWithKML(std::string input_file, std::string kml_file, std::string output_files, double spacing) {
	bool ret = true;
	// Read corner coordinates from KML file.
	// OK to set height to zero here to keep things simple.
	eopcc::PolygonExtent poly_extent = eopcc::ExtentFromKML(kml_file);
	
	// Lat/Long Cube (Really a pyramid extenting from the center of the earth). 
	eopcc::Extent cube_extent = poly_extent.to_extent();

	std::cout << "Opening "<< input_file << std::endl;
	GDALAllRegister();
	
	GDALDataset  *poDataset;
	poDataset = (GDALDataset *) GDALOpen( input_file.c_str() , GA_ReadOnly );
	if( poDataset == NULL ) {
	   std::cerr << input_file << " Does Not Exist" << std::endl;
	   return false;
	}

	for (int band = 1; band <= poDataset->GetRasterCount(); band++) {
		std::cout << band << "/" << poDataset->GetRasterCount();
		std::string output_file(output_files);
		replace(output_file, "(:band)", std::to_string(band));

		GDALRasterBand* raster_band = poDataset->GetRasterBand(band);

		int xdim = raster_band->GetXSize();
	   	int ydim = raster_band->GetYSize();

	    	std::cout << "Image Dims: " << xdim << ", " << ydim << std::endl;
		std::cout << "  " << std::endl;

		std::cout << "PROJ:"<< poDataset->GetGCPProjection() << std::endl;
		std::cout << "  " << std::endl;
	
		char **papszMD = NULL;
		GDALRPCInfo sRPC;
		std::cout << "Getting RPC Info" << std::endl;
		char **papszOptions = NULL;
		papszMD = poDataset->GetMetadata( "RPC" );
		GDALExtractRPCInfo(papszMD, &sRPC);

		void* ptr_transform = GDALCreateRPCTransformer(&sRPC, false, 0.1,  nullptr);

		double min_pixel = xdim;
		double max_pixel = 0;
		double min_line = ydim;
		double max_line = 0;

		double average_z = poly_extent.average_z();

		for (auto line=poly_extent.sides.begin(); line != poly_extent.sides.end(); ++line) {
			double long_to_pixel = line->min_corner().x;
			double lat_to_line = line->min_corner().y;
			double z = average_z;
			int success;

			GDALRPCTransform(ptr_transform, true, 1, &long_to_pixel, &lat_to_line, &z, &success);

			if (min_pixel > long_to_pixel) {
				min_pixel = long_to_pixel;
			}
			if (max_pixel < long_to_pixel) {
				max_pixel = long_to_pixel;
			}

			if (min_line > lat_to_line) {
				min_line = lat_to_line;
			}
			if (max_line < lat_to_line) {
				max_line = lat_to_line;
			}

			long_to_pixel = line->max_corner().x;
			lat_to_line = line->max_corner().y;
			z = average_z;

			GDALRPCTransform(ptr_transform, true, 1, &long_to_pixel, &lat_to_line, &z, &success);

			if (min_pixel > long_to_pixel) {
				min_pixel = long_to_pixel;
			}
			if (max_pixel < long_to_pixel) {
				max_pixel = long_to_pixel;
			}

			if (min_line > lat_to_line) {
				min_line = lat_to_line;
			}
			if (max_line < lat_to_line) {
				max_line = lat_to_line;
			}
		}

		eopcc::CropInfo crop_info;
		eopcc::ImageType img;


		crop_info.pixel_begin = std::max<int>(min_pixel, 0);
		crop_info.pixel_end = std::min<int>(max_pixel, xdim);
		crop_info.line_begin = std::max<int>(min_line, 0);
		crop_info.line_end = std::min<int>(max_line, ydim);

		std::cout << "Crop image  Width: " << crop_info.pixel_begin << " to " << crop_info.pixel_end << std::endl;
		std::cout << "Crop image  Height [from top]: " << crop_info.line_begin << " to " << crop_info.line_end << std::endl;

	
		img.width = std::abs(crop_info.pixel_end - crop_info.pixel_begin) + 1;
		img.height = std::abs(crop_info.line_end - crop_info.line_begin) + 1;

		if (img.height == 0 || img.width == 0) {
		 	std::cerr << "Image does not overlap with KML borders" << std::endl;
		 	return false;
		}
		int min_intensity = 0; 
		int max_intensity = 0;


		char err[1024];
		ret = eopcc::read_cropped_image(input_file.c_str(), img, crop_info, min_intensity, max_intensity, err);
		if (!ret)
			return false;
		std::string extension = output_file.substr(output_file.find_last_of(".") + 1);

		if (extension == "jpeg" || extension == "jpg") {
			ret = eopcc::write_jpeg_file(output_file.c_str(), img, min_intensity, max_intensity, err);
		} else if (extension == "tiff" || extension == "tif") {
			ret = eopcc::write_tiff_file(output_file.c_str(), img, err);
		} else if (extension == "laz" || extension == "las") {
			eopcc::PointCloud sample = eopcc::GenerateSample(kml_file, spacing);
			FillIntensityFromImage(sample, img, crop_info, ptr_transform, min_intensity, 65536.0/(max_intensity - min_intensity));
			eopcc::WriteToLAS(output_file, sample);

		} else {
			std::cerr << "Unrecognized file extension, defaulting to jpeg" << std::endl;
			ret = eopcc::write_jpeg_file(output_file.c_str(), img, min_intensity, max_intensity, err);
		}

		GDALDestroyTransformer(ptr_transform);

	}
	GDALClose(poDataset);

	if (!ret)
		return false;

	return ret;
}



int main(int argc, char* argv[]) {
  try {
    TCLAP::CmdLine cmd("crop-nitf command line", ' ', "1.0");

    TCLAP::UnlabeledValueArg<std::string> input_filename_arg("input", "image file", true,  "", "image file");
    TCLAP::ValueArg<std::string> kml_filename_arg("k", "kml", "KML filename", true, "", "kml file");
    TCLAP::ValueArg<std::string> output_filename_arg("o", "output", "output filename (extension determines type, jpg, tiff, and laz are supported)", true, "", "output file");
     TCLAP::ValueArg<double> spacing_arg("s", "spacing", "output ground spatial density (applies to las/laz files only)", false, 1,
    									"ground spatial density");
    cmd.add(input_filename_arg);
    cmd.add(kml_filename_arg);
    cmd.add(output_filename_arg);
    cmd.add(spacing_arg);
    cmd.parse(argc, argv);

    std::string input_file = input_filename_arg.getValue();
    std::string kml_file = kml_filename_arg.getValue();
    std::string output_file = output_filename_arg.getValue();

	CropImageWithKML(input_file, kml_file, output_file, spacing_arg.getValue());

  } catch (std::exception& e) {
    std::cerr << "error: " << e.what() << std::endl;
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}
