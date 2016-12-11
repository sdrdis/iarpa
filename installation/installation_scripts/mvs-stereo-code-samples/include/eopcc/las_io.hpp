// NOTICES
//
// Copyright (c) 2015 The Johns Hopkins University/
// Applied Physics Laboratory. (JHU/APL)
//
// This material was developed by JHU/APL under U.S. Government contract.
// The U.S. Government has Unlimited Rights in this material per
// DFARS 252.227-7013/7014, as appropriate.
//
// For any other permission, please contact the Legal Office at JHU/APL.
#pragma once

#include <string>

#include <eopcc/cloud.hpp>

namespace eopcc {

const int kLasIncludesRGB = 2;

class LASValidationError : public std::runtime_error { 
public:
	LASValidationError(const char* msg) : std::runtime_error(msg) {}
};


void LoadFromLAS(std::string las_file_name, PointCloud& point_cloud);
void WriteToLAS(std::string las_file_name, const PointCloud& point_cloud);
bool ValidateLAS(std::string las_file_name, std::string kml_file, bool require_compressed);


PolygonExtent ExtentFromKML(const std::string& kml_file);

} // eopcc
