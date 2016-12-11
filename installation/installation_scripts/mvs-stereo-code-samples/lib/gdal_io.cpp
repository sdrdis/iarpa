#include <iostream>
#include <fstream>

#include <eopcc/gdal_io.hpp> 

#include "gdal.h"
#include "gdal_priv.h"
#include "gdal_alg.h"

using namespace std;

namespace eopcc {


// Gdal loads some "driver" libraries dynamically
// this function checks to make sure we've loaded those
  void GdalCheckRegistration() {
    static bool registered = false;

    if (!registered) {
      GDALAllRegister();
    }
  }


// Reads a cropped subsection of an image using GDAL
bool read_cropped_image(const char *imageFileName, ImageType &img, const CropInfo& crop_info, int &min_intensity, 
  int &max_intensity, char *err) {
  GdalCheckRegistration();

  GDALDataset  *poDataset;
  poDataset = (GDALDataset *) GDALOpen(imageFileName, GA_ReadOnly);
  if( poDataset == NULL ) {
    sprintf(err, "%s Does Not Exist\n", imageFileName);
    return false;
  }

  img.bands = poDataset->GetRasterCount();

  // initiate unsigned short img.data 
  img.data.resize(img.height*img.width*img.bands);

  int min_i = crop_info.pixel_begin;
  int min_j = crop_info.line_begin;

  // read a cropped image
  GDALRasterBand *poBand = poDataset->GetRasterBand(1);
  GDALDataType dataType;
  if (poBand) dataType = GDALGetRasterDataType(poBand);

  for (unsigned int j = 0; j < img.height; j++) {
    for (int ib = 0; ib < img.bands; ib++) {
      poBand = poDataset->GetRasterBand(ib+1);
      CPLErr myErr = poBand->RasterIO(GF_Read, min_i, min_j+j, img.width, 1, &img.data[j*img.width + ib], img.width, 1, GDT_UInt16, sizeof(uint16_t)*img.bands, 0);
      if (myErr != CE_None) {
        GDALClose((GDALDatasetH)poDataset);
        return false;
      }

      for (unsigned int icols = 0; icols < img.width; icols++) {
        min_intensity = std::min(min_intensity, (int) img.data[j*img.width + img.bands*icols+ib]);
        max_intensity = std::max(max_intensity, (int) img.data[j*img.width + img.bands*icols+ib]);
      }
    }
  }

  GDALClose(poDataset);
  return true;
}

// Writes out a jpeg file using GDAL
bool write_jpeg_file(const char *FileName, ImageType &img, unsigned int min_intensity, unsigned int max_intensity, char *err) {
  GdalCheckRegistration();

  // Copy img.data into a BYTE one band pixel buffer
  char **papszOptions = NULL;
  unsigned char **image_for_display = NULL;
  image_for_display = new unsigned char*[img.height]; 
  for (unsigned int j=0; j<img.height; j++) {
    image_for_display[j] = new unsigned char[img.width];
  }

  unsigned int pixel;
  unsigned int ii, jj;
  for (unsigned int start_line=0; start_line < img.height; start_line++) {
    if (img.y_backwards) {
      jj = img.height - start_line - 1;
    } else {
      jj = start_line;
    }

    for (unsigned int start_pixel = 0; start_pixel < img.width; start_pixel++) {
      if (img.x_backwards) {
        ii = img.width - start_pixel - 1;
      } else {
        ii = start_pixel;
      }

      pixel = 0;

      for (int k = 0; k < img.bands; k++) {
        pixel = pixel + img.data[jj*img.width + ii+k];
      }

      pixel = pixel/img.bands;
      image_for_display[start_line][start_pixel] =  255*(((double) pixel) - min_intensity)/(max_intensity - min_intensity);
    }
  }


  char **papszMetadata = NULL;
  GDALDriver *pDriverMem = GetGDALDriverManager()->GetDriverByName("MEM");
  GDALDataset *pDsMem = pDriverMem->Create("", img.width, img.height, 1, GDT_Byte, papszMetadata);
  GDALRasterBand *poBand = pDsMem->GetRasterBand(1);
  for(unsigned int j=0;j<img.height;j++)
  {
    CPLErr myErr = poBand->RasterIO(GF_Write, 0, j, img.width, 1, image_for_display[j], img.width, 1, GDT_Byte, 0, 0);
    if (myErr != CE_None) 
    {
      GDALClose((GDALDatasetH)pDsMem);
      sprintf(err, "Error in Writing row %d\n", j);
      return false;
    }
  }
  GDALDriver *pDriver = GetGDALDriverManager()->GetDriverByName("JPEG");
  GDALDataset *pJpegDS = pDriver->CreateCopy(FileName, pDsMem, FALSE, papszMetadata, NULL, NULL);

  GDALClose(pDsMem);
  GDALClose((GDALDatasetH)pJpegDS);
  for (unsigned int j=0;j<img.height;j++) {
    delete[] (image_for_display[j]);
  }
  delete[] image_for_display;

  return true;
}


// Writes out a tiff file using GDAL
bool write_tiff_file(const char *FileName, ImageType &img, char *err) {
  GdalCheckRegistration();
  const char *pszFormat = "GTiff";
  GDALDriver *poDriver;
  char **papszMetadata;
  poDriver = GetGDALDriverManager()->GetDriverByName(pszFormat);
  if(poDriver == NULL)
  {
    sprintf(err, "Can not set driver\n");
    return false;
  }
  // Copy img.data into a BYTE pixel buffer
  char **papszOptions = NULL;

  typedef unsigned short pixel_type;
  pixel_type **image_for_display = NULL;
  image_for_display = new pixel_type*[img.height];  
  unsigned int  buffer = img.width *img.bands;
  for (unsigned int j=0;j<img.height;j++) 
    image_for_display[j] = new pixel_type[buffer];

  unsigned int pixel;
  unsigned int ii, jj;
  for (unsigned int start_line=0; start_line < img.height; start_line++) {
    if (img.y_backwards)
      jj = img.height - start_line - 1;
    else
      jj = start_line;

    for (unsigned int start_pixel = 0; start_pixel < img.width; start_pixel++) {
      if (img.x_backwards) {
        ii = img.width - start_pixel - 1;
      } else {
        ii = start_pixel;
      }

      for (int k = 0; k < img.bands; k++) {
        pixel = img.data[jj*img.width + ii+k];
        image_for_display[start_line][start_pixel+k] = (pixel_type) pixel;
      }
    }
  }

  // write image_for_display into a file
  GDALDataset *poDstDS = poDriver->Create(FileName, img.width, img.height, img.bands, GDT_UInt16, papszOptions);
  for(unsigned int ib=1; ib<=img.bands; ib++) {
    GDALRasterBand *poBand = poDstDS->GetRasterBand(ib);

    for(unsigned int j=0;j<img.height;j++) {
      CPLErr myErr = poBand->RasterIO(GF_Write, 0, j, img.width, 1, image_for_display[j + (ib-1)], 
                                      img.width, 1, GDT_UInt16, 0, 0);
      if (myErr != CE_None) {
        GDALClose((GDALDatasetH)poDstDS);
        sprintf(err, "Error in Writing row %d\n", j);
        return false;
      }
    }
  }
  GDALClose((GDALDatasetH)poDstDS);

  for (unsigned int j=0; j < img.height; j++) {
    delete[] (image_for_display[j]);
  } 
  delete[] image_for_display;

  return true;
}

} // eopcc namespace end