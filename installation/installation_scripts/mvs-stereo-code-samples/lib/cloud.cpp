#include <ogr_spatialref.h>
#include <gdal_priv.h>

#include <eopcc/cloud.hpp>
#include <eopcc/utility.hpp>
#include <eopcc/las_io.hpp>
#include <eopcc/utm_zone.hpp>
#include <eopcc/gdal_io.hpp>

namespace eopcc {


// For a given kml_file (containing a polygon) and a spacing this 
// function generates a PointCloud covering that polygon with spacing meters 
// between points
PointCloud GenerateSample(std::string kml_file, double spacing) {
	PolygonExtent poly_extent = ExtentFromKML(kml_file);
	Extent cube_extent = poly_extent.to_extent();

	OGRSpatialReference pj_utm, pj_latlong;

	// Gets the best zone for the corner of the extent
	int zone = GetUTMZone(cube_extent.min_y, cube_extent.min_x);

	pj_latlong.importFromProj4("+proj=latlong +datum=WGS84");
	pj_utm.importFromProj4("+proj=utm +datum=WGS84");
	
	pj_utm.SetUTM(zone, IsNorthernHemisphere(cube_extent.min_y));
	
	OGRCoordinateTransformation* coordinate_transform;
	coordinate_transform = OGRCreateCoordinateTransformation(&pj_latlong, &pj_utm);

	coordinate_transform->Transform(1, &cube_extent.min_x, &cube_extent.min_y);
	coordinate_transform->Transform(1, &cube_extent.max_x, &cube_extent.max_y);

	PointCloud pc;
	double z = poly_extent.average_z();
	pc.has_time = false;
	pc.has_color = false;

	char* proj4_str;
	pj_utm.exportToProj4(&proj4_str);
	pc.spatial_ref.SetProj4(proj4_str);
	CPLFree(proj4_str);

	int number_x = (cube_extent.max_x - cube_extent.min_x)/spacing + 1;
	int number_y = (cube_extent.max_y - cube_extent.min_y)/spacing + 1;
	pc.resize(number_x * number_y);
	int count = 0;


	for (double x=cube_extent.min_x; x < cube_extent.max_x; x += spacing) {
		for (double y=cube_extent.min_y; y < cube_extent.max_y; y += spacing) {
			pc.loc[count] = Point(x, y, z);
			count++;
		}
	}
	pc.update_extent();

	assert(count == pc.size());

	return pc;
}


} // eopcc namespace end