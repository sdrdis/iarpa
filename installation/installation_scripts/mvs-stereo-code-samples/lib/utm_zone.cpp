#include <eopcc/utm_zone.hpp>

#include <cmath>

namespace eopcc {

// Is the given latitude in the northern hemisphere?
bool IsNorthernHemisphere(double Lat) {
    return Lat >= 0;
}

// Get the UTM zone for a given Lat/Long
int GetUTMZone(double Lat, double Long) { 
    double LongTemp;
    double LongOriginRad;
    int    ZoneNumber;

    /* Make sure the longitude is between -180.00 .. 179.9 */
    LongTemp = fmod( Long, 360 );
    if ( LongTemp < -180 ) LongTemp += 360;
    else if ( LongTemp > 180 ) LongTemp -= 360;

    ZoneNumber = (int)(( LongTemp + 180 ) / 6) + 1;
  
    if ( Lat >= 56.0 && Lat < 64.0 && LongTemp >= 3.0 && LongTemp < 12.0 ) ZoneNumber = 32;

    /* Special zones for Svalbard */
    if ( Lat >= 72.0 && Lat < 84.0 ) 
    {
        if (      LongTemp >=  0.0 && LongTemp <  9.0 ) ZoneNumber = 31;
        else if ( LongTemp >=  9.0 && LongTemp < 21.0 ) ZoneNumber = 33;
        else if ( LongTemp >= 21.0 && LongTemp < 33.0 ) ZoneNumber = 35;
        else if ( LongTemp >= 33.0 && LongTemp < 42.0 ) ZoneNumber = 37;
    }

    return ZoneNumber; 
}

}