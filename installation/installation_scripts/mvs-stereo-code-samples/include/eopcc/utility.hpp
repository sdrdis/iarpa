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
#include <cassert>

#include <vector>
#include <iostream>
#include <utility>
#include <algorithm>
#include <random>

#include <liblas/liblas.hpp>


namespace eopcc {

static const double LAS_TIME_OFFSET = 1e9;
static const int SECONDS_PER_WEEK = 604800;

static double GPSToWeekTime(double gps_time) {
    long long whole_seconds = gps_time;
    double frac_seconds = gps_time - whole_seconds;
    return (whole_seconds % SECONDS_PER_WEEK) + frac_seconds;
}


template<typename T>
inline bool in_range(T val, T start, T end) {
    return (val >= start) && (val < end);
}

inline int to_idx(double val, int index_range) {
  int temp = index_range*val;
  if (temp < 0) {
    return 0;
  }

  if (temp >= index_range) {
    return index_range - 1;
  }

  return temp;
}

// Some basic typedefs to allow precision changing without (hopefully) 
// breaking anything
typedef double pos_type_t;
typedef float intensity_t;
typedef float color_t;

// 3D Point
struct Point {
    pos_type_t x;
    pos_type_t y;
    pos_type_t z;

    Point() { }
    Point(pos_type_t ix, pos_type_t iy, pos_type_t iz) {
        x = ix;
        y = iy;
        z = iz;
    }

    bool operator!=(const Point& other) const {
        return (x != other.x) || (y != other.y) || (z != other.z);
    }

    bool operator==(const Point& other) const {
        return !( operator!=(other) );
    }

    Point operator+(const Point& other) const {
        Point pt;
        pt.x = x + other.x;
        pt.y = y + other.y;
        pt.z = z + other.z;
        return pt;
    }

    Point operator-() const {
        Point neg = (*this);

        neg.x = -x;
        neg.y = -y;
        neg.z = -z;

        return neg;
    }

    Point operator-(const Point& other) const {
        return this->operator+(other.operator-());
    }
};

inline std::ostream& operator<<(std::ostream& o, const Point& pt) {
    o << "(" << pt.x << ", " << pt.y << ", " << pt.z << ")";
    return o;
}

// 3D Surface Normal
struct Normal {
    pos_type_t x;
    pos_type_t y;
    pos_type_t z;
    pos_type_t curvature;
};


// Axis-Aligned 3D Space
struct Extent {
    pos_type_t min_x;
    pos_type_t max_x;
    pos_type_t min_y;
    pos_type_t max_y;
    pos_type_t min_z;
    pos_type_t max_z;

    Extent() {
        min_x = 0.0;
        max_x = 0.0;
        min_y = 0.0;
        max_y = 0.0;
        min_z = 0.0;
        max_z = 0.0;
    }

    Extent(pos_type_t nmin, pos_type_t nmax) {
        min_x = nmin;
        max_x = nmax;
        min_y = nmin;
        max_y = nmax;
        min_z = nmin;
        max_z = nmax;
    }

    Extent(pos_type_t nmin_x, pos_type_t nmax_x,
           pos_type_t nmin_y, pos_type_t nmax_y,
           pos_type_t nmin_z, pos_type_t nmax_z) {
        min_x = nmin_x;
        max_x = nmax_x;
        min_y = nmin_y;
        max_y = nmax_y;
        min_z = nmin_z;
        max_z = nmax_z;
    }

    pos_type_t x_size() {
        return max_x - min_x;
    }
    pos_type_t y_size() {
        return max_y - min_y;
    }
    pos_type_t z_size() {
        return max_z - min_z;
    }

    template <typename T> Point random_sample(T& rand_generator) const {
        std::uniform_real_distribution<> xdis(min_x, max_x);
        std::uniform_real_distribution<> ydis(min_y, max_y);
        std::uniform_real_distribution<> zdis(min_z, max_z);

        Point out;
        out.x = xdis(rand_generator);
        out.y = xdis(rand_generator);
        out.z = xdis(rand_generator);

        return out;
    }


    bool contains(Point& point) const {
        return (min_x <= point.x && point.x <= max_x) &&
               (min_y <= point.y && point.y <= max_y) &&
               (min_z <= point.z && point.z <= max_z);
    }

    Extent operator+(const Point& point) const {
        Extent extent = (*this);
        extent.min_x += point.x;
        extent.min_x += point.x;

        extent.min_y += point.y;
        extent.min_y += point.y;

        extent.min_z += point.z;
        extent.min_z += point.z;
        return extent;
    }

    Point min_corner() const {
        return Point(min_x, min_y, min_z);
    }

    Point max_corner() const {
        return Point(max_x, max_y, max_z);
    }

};


struct Line {
    Point start;
    Point end;

    Line(const Point& pt1, const Point& pt2) {
        if (pt1.y < pt2.y) {
            start = pt1;
            end = pt2;
        } else {
            end = pt1;
            start = pt2;
        }
    }

    Point min_corner() const {
        return Point(std::min(start.x, end.x), std::min(start.y, end.y), std::min(start.z, end.z));
    }

    Point max_corner() const {
        return Point(std::max(start.x, end.x), std::max(start.y, end.y), std::max(start.z, end.z));
    }
};

// Polygon enclosed space
class PolygonExtent {
public:
    std::vector<Line> sides;

    PolygonExtent() { }

    PolygonExtent(const std::vector<Point>& points) {
        for (int i=0; i < points.size() - 1; ++i) {
            sides.push_back(Line(points[i], points[i+1]));
        }
    }
    void MatchCoordinates(const liblas::SpatialReference& spatial_ref);

    pos_type_t average_z() {
        pos_type_t z_sum = 0.0;
        for (int i=0; i < (sides.size() - 1); ++i) {
            z_sum += sides[i].start.z + sides[i].end.z;
        }

        return z_sum / (sides.size() * 2);
    } 

    Extent to_extent() const {
        Extent extent;
        extent.min_x = std::numeric_limits<double>::max();
        extent.min_y = std::numeric_limits<double>::max();
        extent.min_z = -std::numeric_limits<double>::max();

        extent.max_x = -std::numeric_limits<double>::max();
        extent.max_y = -std::numeric_limits<double>::max();
        extent.max_z = std::numeric_limits<double>::max();

        for (const Line& line : sides) {
            if (line.min_corner().x < extent.min_x) {
                extent.min_x = line.min_corner().x;
            }
            if (line.min_corner().y < extent.min_y) {
                extent.min_y = line.min_corner().y;
            }

            if (line.max_corner().x > extent.max_x) {
                extent.max_x = line.max_corner().x;
            }
            if (line.max_corner().y > extent.max_y) {
                extent.max_y = line.max_corner().y;
            }
        }

        return extent;
    }

    bool contains(const Point& point) const;
};



inline std::ostream& operator<<(std::ostream& o, const Extent& extent) {
    o << "E[" << extent.min_x << "," << extent.max_x << " " 
      << extent.min_y << "," << extent.max_y << " "
      << extent.min_z << "," << extent.max_z << "]";
    return o;
}

// Calculates the mean between begin and end
template <typename T, typename Iterator>
T iter_mean(const Iterator& begin, const Iterator& end) {
    T sum = std::accumulate(begin, end, (T)0.0);
    return sum / std::distance(begin, end);
}

// Calculates the variance between begin and end
template <typename T, typename Iterator>
T iter_var(const Iterator& begin, const Iterator& end) {
    T mean = iter_mean<T>(begin, end);

    T accum = 0.0;
    std::for_each(begin, end, [&](const T d) {
        accum += (d - mean)*(d - mean);
    });

    return accum / (std::distance(begin, end)-1);
}

// Calculates the stdev between begin and end
template <typename T, typename Iterator>
T iter_stdev(const Iterator& begin, const Iterator& end) {
    return std::sqrt(iter_var<T>(begin, end));
}


template <typename T>
T vector_mean(const std::vector<T>& values) {
    return iter_mean<T>(values.begin(), values.end());
}

template <typename T>
T vector_var(const std::vector<T>& values) {
    return iter_var<T>(values.begin(), values.end());
}

template <typename T>
T vector_stdev(const std::vector<T>& values) {
    return iter_stdev<T>(values.begin(), values.end());
}





} // namespace eopcc