#pragma once

#include <eopcc/utility.hpp>

namespace eopcc {

void GdalCheckRegistration();

struct CropInfo {
	int pixel_begin;
	int pixel_end;
	int line_begin;
	int line_end;
};

struct ImageType {
	int width;
	int height;
	int bands;
	std::vector<uint16_t> data;
	bool x_backwards, y_backwards;

	ImageType () {
		x_backwards = false;
		y_backwards = false;
	}
};


bool read_cropped_image(const char *imageFileName, ImageType &img, const CropInfo& crop_info, 
						 int& min_intensity,  int& max_intensity, char *err);
bool write_jpeg_file(const char *FileName, ImageType &img, unsigned int min_intensity, unsigned int max_intensity, char *err);
bool write_tiff_file(const char *FileName, ImageType &img, char *err);


} // end namespace eopcc