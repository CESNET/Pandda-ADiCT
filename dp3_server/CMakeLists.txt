cmake_minimum_required(VERSION 3.12)

project(pandda_adict DESCRIPTION "ADiCT lite server for PANDDA project" LANGUAGES NONE)

add_custom_target(adict ALL)
install(DIRECTORY "${PROJECT_SOURCE_DIR}/config" DESTINATION ".")
install(DIRECTORY "${PROJECT_SOURCE_DIR}/modules" DESTINATION "."
    PATTERN "*/__pycache__" EXCLUDE)

# Ensure presence of version specifier
if(NOT DEFINED package_version)
    message(FATAL_ERROR "Variable `package_version` is not set!")
endif()

# CPack configuration for RPM packaging
set(CPACK_GENERATOR "RPM")
set(CPACK_SOURCE_GENERATOR "RPM")
set(CPACK_PACKAGE_NAME pandda_adict)
set(CPACK_PACKAGE_CONTACT "Ondřej Sedláček <ondrej.sedlacek@cesnet.cz>")
set(CPACK_PACKAGE_VENDOR "CESNET z.s.p.o.")
set(CPACK_PACKAGE_VERSION "${package_version}")
set(CPACK_PACKAGE_RELEASE 1)
set(CPACK_PACKAGING_INSTALL_PREFIX "/opt/adict")
set(CPACK_RPM_PACKAGE_ARCHITECTURE "noarch")
set(CPACK_RPM_PACKAGE_RELOCATABLE OFF)
set(CPACK_RPM_PACKAGE_REQUIRES "")
set(CPACK_RPM_BUILDREQUIRES "cmake >= 3.12")
set(CPACK_RPM_PACKAGE_LICENSE "BSD-3-Clause")
set(CPACK_RPM_SOURCE_PKG_BUILD_PARAMS "-Dpackage_version=${package_version}")
set(CPACK_SOURCE_IGNORE_FILES "build;\.env;\.venv;env;venv;__pycache__")

include(CPack)
