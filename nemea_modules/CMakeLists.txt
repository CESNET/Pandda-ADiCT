cmake_minimum_required(VERSION 3.12)

project(adict_nemea_packages VERSION 1.0.0 DESCRIPTION "NEMEA Packages for ADiCT" LANGUAGES NONE)

add_subdirectory(common)
add_subdirectory(dp_aggregator)
add_subdirectory(ip_activity2)
add_subdirectory(nemea_adict_sender)
add_subdirectory(open_ports)
add_subdirectory(recog)

# Ensure presence of version specifier
if(NOT DEFINED package_version)
    message(FATAL_ERROR "Variable `package_version` is not set!")
endif()

set(CMAKE_INSTALL_PREFIX "/usr")

# CPack configuration for RPM packaging
set(CPACK_GENERATOR "RPM")
set(CPACK_SOURCE_GENERATOR "RPM")
set(CPACK_PACKAGE_NAME "nemea-adict")
set(CPACK_PACKAGE_CONTACT "Ondrej Sedlacek <ondrej.sedlacek@cesnet.cz>")
set(CPACK_PACKAGE_VENDOR "CESNET z.s.p.o.")
set(CPACK_PACKAGE_VERSION "${package_version}")
set(CPACK_PACKAGE_RELEASE 1)
set(CPACK_PACKAGING_INSTALL_PREFIX "/usr/bin")
set(CPACK_RPM_PACKAGE_ARCHITECTURE "noarch")
set(CPACK_RPM_PACKAGE_REQUIRES "python3-nemea-pytrap")
set(CPACK_RPM_BUILDREQUIRES "cmake >= 3.12")
set(CPACK_RPM_PACKAGE_LICENSE "BSD-3-Clause")
set(CPACK_RPM_SOURCE_PKG_BUILD_PARAMS "-Dpackage_version=${package_version}")
set(CPACK_SOURCE_IGNORE_FILES "build;\.env;\.venv;env;venv;__pycache__")

include(CPack)
