cmake_minimum_required(VERSION 3.12)

project(adict_nemea_packages VERSION 1.0.0 DESCRIPTION "NEMEA Packages for ADiCT")

include(../cmake/build_type.cmake)
include(../cmake/installation.cmake)

# Ensure presence of version specifier
if(NOT DEFINED package_version)
    message(FATAL_ERROR "Variable `package_version` is not set!")
endif()

add_subdirectory(common)
add_subdirectory(dp_aggregator)
add_subdirectory(ip_activity2)
add_subdirectory(nemea_adict_sender)
add_subdirectory(open_ports)
add_subdirectory(recog)

# CPack configuration for RPM packaging
include(InstallRequiredSystemLibraries)
set(CPACK_PACKAGE_NAME "nemea-adict")
set(CPACK_PACKAGE_VERSION "${package_version}")
set(CPACK_PACKAGE_RELEASE 1)
set(CPACK_PACKAGE_CONTACT "Ondrej Sedlacek <ondrej.sedlacek@cesnet.cz>")
set(CPACK_PACKAGE_VENDOR "CESNET z.s.p.o.")
set(CPACK_INSTALL_PREFIX "/usr")
set(CPACK_PACKAGING_INSTALL_PREFIX "/usr/bin")
set(CPACK_RPM_PACKAGE_REQUIRES "python3-nemea-pytrap")

include(CPack)
