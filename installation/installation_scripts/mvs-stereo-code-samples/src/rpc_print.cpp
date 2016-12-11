#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>

#include <gdal.h>
#include <gdal_priv.h>
#include <gdal_alg.h>

#include <ogr_spatialref.h>

#include <tclap/CmdLine.h>


// VS2012 doesn't have round 
#ifdef WIN32
	int round(double val) {
		return (val < 0) ? ceil(val - 0.5) : floor(val + 0.5);
	}
#else
	using std::round;
#endif




bool PrintRPCMetadata(std::string nitf_file) {
  // Register all the GDAL drivers (required for GDAL to function)
	GDALAllRegister();

	GDALDataset  *gdal_dataset;
	gdal_dataset = (GDALDataset *) GDALOpen(nitf_file.c_str() , GA_ReadOnly);
  if( gdal_dataset == nullptr) {
    std::cerr << nitf_file << " Does Not Exist" << std::endl;
    return false;
  }

	char **papszMD = NULL;
	GDALRPCInfo rpc_info;

	papszMD = gdal_dataset->GetMetadata( "RPC" );
	GDALExtractRPCInfo(papszMD, &rpc_info);

  // GDALRPCInfo is a structure containing the RPC metadata
  // see http://www.gdal.org/structGDALRPCInfo.html for full list of members

  std::cout << "dfLINE_OFF " << rpc_info.dfLINE_OFF << "\n";
  std::cout << "dfSAMP_OFF " << rpc_info.dfSAMP_OFF << "\n";
  std::cout << "dfMIN_LAT " << rpc_info.dfMIN_LAT << "\n";
  std::cout << "dfMIN_LONG " << rpc_info.dfMIN_LONG << "\n";

  std::cout << "\nadfLINE_NUM_COEFF: \n";
  for (int i=0; i < 20; ++i) {
    std::cout << rpc_info.adfLINE_NUM_COEFF[i] << " ";
  }
  std::cout << std::endl << std::endl;

  std::cout << "adfSAMP_DEN_COEFF: \n";
  for (int i=0; i < 20; ++i) {
    std::cout << rpc_info.adfSAMP_DEN_COEFF[i] << " ";
  }
  std::cout << std::endl << std::endl;


  // This is a world to image coordinate transformer based on the RPC metadata
  // more documentation is here: http://www.gdal.org/gdal__alg_8h.html#af4c3c0d4c79218995b3a1f0bac3700a0 
	void* ptr_transform = GDALCreateRPCTransformer(&rpc_info, false, 0.1,  nullptr);


	GDALDestroyTransformer(ptr_transform);
	GDALClose(gdal_dataset);

	return true;
}



int main(int argc, char* argv[]) {
  if (argc != 2) {
    std::cout << "Usage: " << argv[0] << " <nitf file>" << std::endl;
    return EXIT_FAILURE;
  }

  PrintRPCMetadata(argv[1]);

  return EXIT_SUCCESS;
}
