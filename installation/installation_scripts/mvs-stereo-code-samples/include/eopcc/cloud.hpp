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

#include <cmath>
#include <vector>
#include <iostream>
#include <utility>
#include <iterator>
#include <limits>

#include <liblas/header.hpp>

#include <eopcc/utility.hpp>

namespace eopcc {

template <typename T>
struct PointColor {
    T red;
    T green;
    T blue;

    T intensity() {
        return red*red + green*green + blue*blue;
    }
};


struct PointCloud {
    liblas::SpatialReference spatial_ref;
    Extent extent;

    std::vector<Point> loc;
    std::vector<intensity_t> intensity;

    // These three vectors are fairly specific to handling and tracking 
    // multiple returns in LiDAR data
    std::vector<unsigned char> num_returns;
    std::vector<unsigned char> return_num;
    std::vector<bool> scan_edge;

    // Color is optional (not all point clouds use it)
    bool has_color;
    std::vector<PointColor<color_t>> color;

    // Time is optional. If it is included it is the gps time
    // each point was collected during
    bool has_time;
    std::vector<double> gps_time;

    PointCloud() {
        has_time = true;
        has_color = true;
    }

    void resize(size_t num_points) {
        loc.resize(num_points);
        intensity.resize(num_points);

        if (has_color) {
            color.resize(num_points);
        }

        if (has_time) {
            gps_time.resize(num_points);
        }

        num_returns.resize(num_points);
        return_num.resize(num_points);
        scan_edge.resize(num_points);
    }

    size_t size() const {
        return loc.size();
    }


    void set_from(int index, const PointCloud& other, int other_index) {
        loc[index] = other.loc[other_index];
        intensity[index] = other.intensity[other_index];
        num_returns[index] = other.num_returns[other_index];
        return_num[index] = other.return_num[other_index];
        scan_edge[index] = other.scan_edge[other_index];

        if (has_color && other.has_color) {
            color[index] = other.color[other_index];
        }

        if (has_time && other.has_time) {
            gps_time[index] = other.gps_time[other_index];
        }
    }

    // Generates a subcloud containing points between a staring index
    // (sub_start) and an ending index exclusive (sub_end)
    PointCloud subcloud(int sub_start, int sub_end) {
        PointCloud out_cloud;
        out_cloud = (*this);

        size_t num_valid = sub_end - sub_start;

        out_cloud.resize(num_valid);

        for (size_t in_index=sub_start; in_index < sub_end; ++in_index) {
            out_cloud.set_from(in_index - sub_start, (*this), in_index);
        }

        return out_cloud;
    }

    // The mean location of the point cloud
    Point mean() const {
        Point mean;
        mean.x = 0;
        mean.y = 0;
        mean.z = 0;

        for (const Point& pt : loc) {
            mean = mean + pt;
        }

        mean.x /= loc.size();
        mean.y /= loc.size();
        mean.z /= loc.size();


        return mean;
    }

    // Applies a tranlation to the point cloud
    void translate(const Point& translation) {
        for (Point& pt : loc) {
            pt = pt + translation;
        }

        extent = extent + translation;
    }

    // Given a vector of keep/trash flags creates a new vector with only the keep members
    PointCloud filter(const std::vector<bool>& filter_vector) const;

    // Given a vector of keep/trash flags removes trash members from cloud
    void filter_inplace(const std::vector<bool>& filter_vector);

    // Recalucates the extent of the PointCloud and returns it
    Extent calculate_extent() const {
        pos_type_t x_min = std::numeric_limits<pos_type_t>::max();
        pos_type_t y_min = std::numeric_limits<pos_type_t>::max();
        pos_type_t z_min = std::numeric_limits<pos_type_t>::max();
        pos_type_t x_max = -std::numeric_limits<pos_type_t>::max();
        pos_type_t y_max = -std::numeric_limits<pos_type_t>::max();
        pos_type_t z_max = -std::numeric_limits<pos_type_t>::max();
        for (size_t i=0; i < loc.size(); ++i) {
            if (loc[i].x < x_min) {
                x_min = loc[i].x;
            }
            if (loc[i].y < y_min) {
                y_min = loc[i].y;
            }
            if (loc[i].z < z_min) {
                z_min = loc[i].z;
            }

            if (loc[i].x > x_max) {
                x_max = loc[i].x;
            }
            if (loc[i].y > y_max) {
                y_max = loc[i].y;
            }
            if (loc[i].z > z_max) {
                z_max = loc[i].z;
            }
        }

        Extent t_extent;

        t_extent.min_x = x_min;
        t_extent.max_x = x_max;
        t_extent.min_y = y_min;
        t_extent.max_y = y_max;
        t_extent.min_z = z_min;
        t_extent.max_z = z_max;

        return t_extent;
    }

    // Recalucates the extent of the PointCloud and updates the extent
    void update_extent() {
        extent = calculate_extent();
    }

    // Counts points in the cloud contained in the extent
    int inside_extent(const Extent& extent);
    // Counts points in the cloud contained in the extent
    int inside_extent(const PolygonExtent& extent);
};

PointCloud GenerateSample(std::string kml_file, double spacing);

} // namespace eopcc