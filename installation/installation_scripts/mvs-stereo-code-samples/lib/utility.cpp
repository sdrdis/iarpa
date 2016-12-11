#include <eopcc/utility.hpp>

#include <liblas/liblas.hpp>

// GDAL includes
#include <gdal_priv.h>
#include <ogr_spatialref.h>

namespace eopcc {

// Converts a PolygonExtent in LatLon coordinates to the coordinate system of
// the given spatial_ref
void PolygonExtent::MatchCoordinates(const liblas::SpatialReference& spatial_ref) {
  OGRSpatialReference utm_srs(spatial_ref.GetWKT().c_str());
  OGRSpatialReference latlon_srs;
  latlon_srs.CopyGeogCSFrom(&utm_srs);

  OGRCoordinateTransformation* coordinate_transform;

  coordinate_transform = OGRCreateCoordinateTransformation(&latlon_srs, &utm_srs);

  for (eopcc::Line& line : sides) {
    coordinate_transform->Transform(1, &line.start.x, &line.start.y);
    coordinate_transform->Transform(1, &line.end.x, &line.end.y);
  }
}

// Checks for intersection between a ray along the x axis starting at
// the point and line. The is a detail method used to test a point
// for containment in a polygon. 
// See: https://en.wikipedia.org/wiki/Point_in_polygon#Ray_casting_algorithm
bool ray_intersects_segment(Point point, const Line& line) {
	const double epsilon = std::numeric_limits<double>::min();
	Point lower = line.start; 
	Point upper = line.end; 

	if (point.y == lower.y || point.y == upper.y) {
		point.y += epsilon;
	}

	if (point.y < lower.y || point.y > upper.y) { 
		return false;
	} else if (point.x > std::max(lower.x, upper.x)) {
		return false;
	} else {
		if (point.x < std::min(lower.x, upper.x)) {
			return true;
		} else {
			double m_line;
			double m_ray;
			if (lower.x != upper.x) {
				m_line = (upper.y - lower.y)/(upper.x - lower.x);
			} else {
				m_line = std::numeric_limits<double>::max();
			}
			if (lower.x != point.x) {
				m_ray = (point.y - lower.y)/(point.x - lower.x);
			} else {
				m_ray = std::numeric_limits<double>::max();
			}
			if (m_ray >= m_line) {
				return true;
			} else {
				return false;
			}
		}
	}
}

// Does the (2D) Polygon contain the given point. Point and polygon must have
// the same coordinates system
bool PolygonExtent::contains(const Point& point) const {
	int intersection_count = 0;

	for (const Line& line : sides) {
		if (ray_intersects_segment(point, line)) {
			intersection_count++;
		}
	}

	// If the intesection count is odd, the point is inside the polygon
	return (intersection_count % 2 == 1);
}


}