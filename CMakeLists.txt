cmake_minimum_required(VERSION 3.12)

project(adict_nemea_packages VERSION 1.0.0 DESCRIPTION "NEMEA Packages for ADiCT")

include(cmake/build_type.cmake)
include(cmake/installation.cmake)

add_subdirectory(nemea_modules)

# CPack configuration for RPM packaging
include(InstallRequiredSystemLibraries)
set(CPACK_PACKAGE_NAME adict_modules)
set(CPACK_PACKAGE_VERSION "${PROJECT_VERSION}")
set(CPACK_PACKAGE_RELEASE 1)
set(CPACK_PACKAGE_CONTACT "Ondrej Sedlacek <ondrej.sedlacek@cesnet.cz>")
set(CPACK_PACKAGE_VENDOR "CESNET z.s.p.o.")
set(CPACK_INSTALL_PREFIX "/usr")
set(CPACK_PACKAGING_INSTALL_PREFIX "/usr/bin")
set(CPACK_RPM_POST_INSTALL_SCRIPT_FILE "${CMAKE_CURRENT_SOURCE_DIR}/scripts/post_install.sh")

include(CPack)
