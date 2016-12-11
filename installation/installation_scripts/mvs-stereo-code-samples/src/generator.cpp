#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>

#include <tclap/CmdLine.h>

#include <eopcc/utility.hpp>
#include <eopcc/las_io.hpp>
#include <eopcc/utm_zone.hpp>
#include <eopcc/gdal_io.hpp>


// This is a very simple program to generate a las file that will pass
// validation. If you want something you can actually view, use crop-nitf with
// .las or .laz as the output extension
int main(int argc, char* argv[]) {
  try {
    TCLAP::CmdLine cmd("las-generator command line", ' ', "1.0");

    TCLAP::UnlabeledValueArg<std::string> input_filename_arg("input", "image file", false,  "", "image file");
    TCLAP::ValueArg<std::string> kml_filename_arg("k", "kml", "KML filename", true, "", "kml file");
    TCLAP::ValueArg<std::string> output_filename_arg("o", "output", "output image filename", true, "", 
    												 "output image file");
    TCLAP::ValueArg<double> spacing_arg("s", "spacing", "output ground spatial density", false, 1,
    									"ground spatial density");
    cmd.add(input_filename_arg);
    cmd.add(kml_filename_arg);
    cmd.add(output_filename_arg);
    cmd.add(spacing_arg);
    cmd.parse(argc, argv);

    std::string input_file = input_filename_arg.getValue();
    std::string kml_file = kml_filename_arg.getValue();
    std::string output_file = output_filename_arg.getValue();

	eopcc::PointCloud pc = eopcc::GenerateSample(kml_file, spacing_arg.getValue());
	eopcc::WriteToLAS(output_file, pc);

  } catch (std::exception& e) {
    std::cerr << "error: " << e.what() << std::endl;
    return EXIT_FAILURE;
  }

  return EXIT_SUCCESS;
}