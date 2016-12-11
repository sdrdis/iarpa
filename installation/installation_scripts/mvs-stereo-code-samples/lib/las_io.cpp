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


#include <eopcc/las_io.hpp>

#include <liblas/liblas.hpp>
#include <liblas/point.hpp>
#include <liblas/reader.hpp>
#include <liblas/writer.hpp>
#include <liblas/color.hpp>

#include <gdal_priv.h>
#include <tinyxml/tinyxml2.h>



namespace eopcc {


// Validates that a LAS/LAZ file can be opened and is inside the bounds
// outlined by the given kml_file. If require_compressed is true an
// exception is throw if the given file is not LAZ formatted
bool ValidateLAS(std::string las_file_name, std::string kml_file, bool require_compressed) {
    std::ifstream ifs;
    if (!liblas::Open(ifs, las_file_name)) {
        throw LASValidationError("No such file exists.");
    }

    PolygonExtent extent;
    bool extent_valid = !kml_file.empty();

    if (extent_valid) {
        try {
            extent = ExtentFromKML(kml_file);
        } catch (std::runtime_error& e) {
            extent_valid = false;
        }
    }

    liblas::ReaderFactory factory;
    liblas::Reader reader = factory.CreateWithStream(ifs);
    liblas::Header const& header = reader.GetHeader();

    liblas::PointFormatName ptformat = header.GetDataFormatId();
    liblas::SpatialReference spatial_ref =  header.GetSRS();
    size_t num_points = header.GetPointRecordsCount();

    std::string proj4_str = spatial_ref.GetProj4();
    if (proj4_str.empty()) {
      throw LASValidationError("File opened, but SpatialReference is invalid");
    } else {
        std::cout << "Found spatial reference: " << proj4_str << std::endl;
    }

    if (extent_valid) {
        extent.MatchCoordinates(spatial_ref);
    }

    if (num_points < 1) {
      throw LASValidationError("File opened, but no points found");
    }

    int inbounds_count = 0;
    for (size_t index=0; index < num_points; ++index) {
        if(!reader.ReadNextPoint()) {
           throw LASValidationError("Number of points in header greater than points in file");
        }
        liblas::Point const& point = reader.GetPoint();

        Point pt;
        pt.x = point.GetX();
        pt.y = point.GetY();
        pt.z = point.GetZ();

        if (extent_valid) {
            if (extent.contains(pt)) {
                inbounds_count++;
            }
        }
    }

    if (extent_valid) {

        if (inbounds_count == 0) {
            throw LASValidationError("No points inside KML bounds");
        }

        std::cout << "Tested bounds: " << ((double)inbounds_count) / num_points * 100 << "% of points inside KML bounds" << std::endl;
    }

    if (require_compressed && !header.Compressed()) {
        throw LASValidationError("Compression not found (is .las instead of .laz)");
    }


    return true;
}


// Fills the given point_cloud using a LAS/LAZ file
// Note that the entire file will be unpacked and uncompressed then
// stored in memory
void LoadFromLAS(std::string las_file_name, PointCloud& point_cloud) {
    std::ifstream ifs;
    if (!liblas::Open(ifs, las_file_name)) {
        throw std::runtime_error("Failed to open " + las_file_name);
    }

    liblas::ReaderFactory factory;
    liblas::Reader reader = factory.CreateWithStream(ifs);
    liblas::Header const& header = reader.GetHeader();


    liblas::PointFormatName ptformat = header.GetDataFormatId();
    point_cloud.spatial_ref = header.GetSRS();

    if (ptformat >= kLasIncludesRGB) {
        point_cloud.has_color = true;
    } else {
        point_cloud.has_color = false;
    }


    point_cloud.resize(header.GetPointRecordsCount());
    point_cloud.extent.min_x = header.GetMinX();
    point_cloud.extent.max_x = header.GetMaxX();

    point_cloud.extent.min_y = header.GetMinY();
    point_cloud.extent.max_y = header.GetMaxY();

    point_cloud.extent.min_z = header.GetMinZ();
    point_cloud.extent.max_z = header.GetMaxZ();



    for (size_t index=0; index < point_cloud.size(); ++index) {
        if(!reader.ReadNextPoint()) {
            throw std::runtime_error("Failed to read point");
        }
        liblas::Point const& point = reader.GetPoint();

        if (ptformat % 2 == 1) {
            point_cloud.gps_time[index] = point.GetTime();
        }

        point_cloud.loc[index].x = point.GetX();
        point_cloud.loc[index].y = point.GetY();
        point_cloud.loc[index].z = point.GetZ();

        if (ptformat >= kLasIncludesRGB) {
            liblas::Color color = point.GetColor();

            point_cloud.color[index].red = color[0] / 65536.0;
            point_cloud.color[index].green = color[1] / 65536.0;
            point_cloud.color[index].blue = color[2] / 65536.0;
        }

        point_cloud.intensity[index] = point.GetIntensity();

        point_cloud.return_num[index] = point.GetReturnNumber();
        point_cloud.num_returns[index] = point.GetNumberOfReturns();
        point_cloud.scan_edge[index] = point.GetFlightLineEdge();
    }
}

// Write a PointCloud out as a LAS/LAZ file. Compression to laz is 
// determined by the file extension (more specifically if the extension 
// ends in z)
void WriteToLAS(std::string las_file_name, const PointCloud& point_cloud) {
    std::ofstream ofs;
    if (!liblas::Create(ofs, las_file_name))
    {
        throw std::runtime_error(std::string("Can not create ") + las_file_name);
    }

    Extent extent = point_cloud.calculate_extent();

    liblas::Header header;

    // Checks if the filename extension ends in z and enables compression if
    // it does
    if (las_file_name.back() == 'z') {
        header.SetCompressed(true);
    } else {
        header.SetCompressed(false); 
    }

    header.SetMax(extent.max_x, extent.max_y, extent.max_z);
    header.SetMin(extent.min_x, extent.min_y, extent.min_z);


    // Calculates an good scale and offset to reduce quatization error when
    // the points are packed into the file (LAS format stores positions as
    // 32 bit integers)
    double scale_x = ((extent.max_x - extent.min_x)/2.0) / std::numeric_limits<int32_t>::max();
    double scale_y = ((extent.max_y - extent.min_y)/2.0) / std::numeric_limits<int32_t>::max();
    double scale_z = ((extent.max_z - extent.min_z)/2.0) / std::numeric_limits<int32_t>::max();

    // Offset at the center minimizes quatization error
    double offset_x = (extent.max_x - extent.min_x)/2.0 + extent.min_x;
    double offset_y = (extent.max_y - extent.min_y)/2.0 + extent.min_y;
    double offset_z = (extent.max_z - extent.min_z)/2.0 + extent.min_z;

    header.SetScale(scale_x, scale_y, scale_z);
    header.SetOffset(offset_x, offset_y, offset_z);

    // Specify the LAS format as 1.2
    header.SetVersionMajor(1);
    header.SetVersionMinor(2);

    if (point_cloud.has_color) {
        if (point_cloud.has_time) {
            header.SetDataFormatId(liblas::ePointFormat3);
        } else {
            header.SetDataFormatId(liblas::ePointFormat2);
        }
    } else {
        if (point_cloud.has_time) {
            header.SetDataFormatId(liblas::ePointFormat1);
        } else {
            header.SetDataFormatId(liblas::ePointFormat0);
        }
    }
    header.SetPointRecordsCount(point_cloud.size());

    // Both these lines are needed to update the georefence from the spatial_ref
    // stored in the point cloud
    header.SetSRS(const_cast<liblas::SpatialReference&>(point_cloud.spatial_ref));
    header.SetGeoreference();

    liblas::Writer writer(ofs, header);

    for (size_t i=0; i < point_cloud.size(); ++i) {
        liblas::Point point(&header);
        point.SetCoordinates(point_cloud.loc[i].x, point_cloud.loc[i].y, point_cloud.loc[i].z);
        if (point_cloud.has_time) {
            point.SetTime(point_cloud.gps_time[i]);
        }

        if (point_cloud.has_color) {
            liblas::Color color;
            color[0] = to_idx(point_cloud.color[i].red, std::numeric_limits<uint16_t>::max() - 1);
            color[1] = to_idx(point_cloud.color[i].green, std::numeric_limits<uint16_t>::max() - 1);
            color[2] = to_idx(point_cloud.color[i].blue, std::numeric_limits<uint16_t>::max() - 1);
            point.SetColor(color);
        }

        point.SetIntensity(point_cloud.intensity[i]);

        point.SetReturnNumber(point_cloud.return_num[i]);
        point.SetNumberOfReturns(point_cloud.num_returns[i]);
        point.SetFlightLineEdge(point_cloud.scan_edge[i]);

        writer.WritePoint(point);
    }

    writer.WriteHeader();
}



PolygonExtent ExtentFromKML(const std::string& kml_file) {
	using namespace tinyxml2;

	XMLDocument doc;
	XMLError err = doc.LoadFile(kml_file.c_str());

    if (err) {
        throw std::runtime_error(kml_file + " doesn't exist");
    }
	
	XMLElement* root_element = doc.RootElement();


	const char* nodeName = root_element->Value();
	XMLNode* document =  root_element->FirstChildElement("Document");
	if (!document) {
		throw std::runtime_error("Failed to parse document");
	}

	XMLNode *placemark =  document->LastChildElement("Placemark");
	if (!placemark)
	{
		throw std::runtime_error("Failed to parse placemark");
	}

	XMLNode* polygon =  placemark->LastChildElement("Polygon");
	if (!polygon)
	{
		throw std::runtime_error("Failed to parse polygon");
	}

	XMLNode *outer_boundary_is =  polygon->FirstChildElement("outerBoundaryIs");
	if (!outer_boundary_is)
	{
		throw std::runtime_error("Failed to parse outerBoundaryIs");
	}

	XMLNode* linear_ring =  outer_boundary_is->FirstChildElement("LinearRing");
	if (!linear_ring)
	{
		throw std::runtime_error("Failed to parse LinearRing");
	}

	XMLNode *coords =  linear_ring->FirstChild ();
	if (!coords)
	{
		throw std::runtime_error("Failed to parse coords");
	}

	XMLNode *xml_contents = coords->FirstChild();
	if (!xml_contents) {
		throw std::runtime_error("Failed to parse coords contents");
	}

	std::string contents = xml_contents->Value();


	std::vector<Point> points;

	std::stringstream ss;
	ss << contents;

	for (;;) {
		std::string value;
		Point pt;

		try {
			std::getline(ss, value, ',');
			pt.x = std::stod(value);
			std::getline(ss, value, ',');
			pt.y = std::stod(value);
			std::getline(ss, value, '\n');
			pt.z = std::stod(value);
		} catch (std::invalid_argument& e) {
			break;
		}
		
		points.push_back(pt);
	}

	PolygonExtent poly(points);
	return poly;
}

//
///// Reads a polygon from a KML file using libkml
///// libkml is pretty annoying to build on Windows
///// so it is not built in the sample project
//PolygonExtent ExtentFromKML(const std::string& kml_file) {
//  std::ifstream file(kml_file);
//
//  std::string errors;
//
//  auto stream = kmlengine::KmlStream::ParseFromIstream(&file, &errors, nullptr);
//  auto element = stream->get_root();
//  const kmldom::KmlPtr kml = kmldom::AsKml(element);
//  const kmldom::FeaturePtr feature = kml->get_feature();
//
//  std::vector<Point> points;
//
//  if (feature->Type() == kmldom::Type_Document) {
//    const kmldom::DocumentPtr doc = kmldom::AsDocument(feature);
//
//    for (int i=0; i < doc->get_feature_array_size(); ++i) {
//        kmldom::FeaturePtr feature = doc->get_feature_array_at(i);
//        if (feature->Type() == kmldom::Type_Placemark) {
//            kmldom::PlacemarkPtr placemark = kmldom::AsPlacemark(feature);
//
//            kmldom::GeometryPtr geo = placemark->get_geometry();
//
//            if (geo && geo->Type() == kmldom::Type_Polygon) {
//                kmldom::PolygonPtr poly = kmldom::AsPolygon(geo);
//                kmldom::OuterBoundaryIsPtr outer_bound = poly->get_outerboundaryis();
//                kmldom::LinearRingPtr linear_ring = outer_bound->get_linearring();
//                kmldom::CoordinatesPtr coords = linear_ring->get_coordinates();
//
//                if (coords) {
//                    for (int i=0; i < coords->get_coordinates_array_size(); ++i) {
//                        Point pt;
//                        auto vec3 = coords->get_coordinates_array_at(i);
//                        pt.x = vec3.get_longitude();
//                        pt.y = vec3.get_latitude();
//                        pt.z = vec3.get_altitude();
//                        points.push_back(pt);
//                    }
//
//                    return PolygonExtent(points);
//                }
//            }
//        }
//    }
//
//  } else {
//    throw std::runtime_error("KML failed to parse");
//  }
//  throw std::runtime_error("No Polygon found in KML");  
//}


} // end eopcc
