#include <tclap/CmdLine.h>
#include <eopcc/las_io.hpp>


// A simple command line wrapper around the ValidateLAS function. 
int main(int argc, char* argv[]) {
  try {
    TCLAP::CmdLine cmd("las-validator command line", ' ', "1.0");

    TCLAP::UnlabeledValueArg<std::string> las_filename_arg("input", "las/laz file", true,  "", "las/laz file");
    TCLAP::ValueArg<std::string> kml_filename_arg("k", "kml", "KML filename", false, "", "kml file");
    cmd.add(las_filename_arg);
    cmd.add(kml_filename_arg);
    cmd.parse(argc, argv);

    std::string input_file = las_filename_arg.getValue();
    std::string kml_file = kml_filename_arg.getValue();

    eopcc::ValidateLAS(input_file, kml_file, true);
    
  } catch (eopcc::LASValidationError& validation_error) {
    std::cerr << "Validation error: " << validation_error.what() << std::endl;
    return EXIT_FAILURE;
  } catch (std::exception& e) {
    std::cerr << "error: " << e.what() << std::endl;
    return EXIT_FAILURE;
  }

  std::cout << "Tests passed, file is valid." << std::endl;
  return EXIT_SUCCESS;
}
