cmake_minimum_required(VERSION 3.12)

project(pandda_frontend DESCRIPTION "User interface for PANDDA project")

add_custom_target(frontend ALL COMMAND npm install && npm run build)
install(DIRECTORY "${PROJECT_SOURCE_DIR}/dist/" DESTINATION ".")

# Parse version from package.json
file(READ "${PROJECT_SOURCE_DIR}/package.json" package_json)
string(REGEX MATCH "\"version\":[ \t\n]*\"([^\"]+)\"" _ ${package_json})
set(package_json_version ${CMAKE_MATCH_1})
if (NOT package_json_version)
    message(FATAL_ERROR "Couldn't parse version from package.json")
endif(NOT package_json_version)

# CPack configuration for RPM packaging
set(CPACK_GENERATOR "RPM")
set(CPACK_PACKAGE_CONTACT "Dávid Benko <benko@cesnet.cz>")
set(CPACK_PACKAGE_NAME pandda_frontend)
set(CPACK_PACKAGE_RELEASE 1)
set(CPACK_PACKAGE_VENDOR "CESNET z.s.p.o.")
set(CPACK_PACKAGE_VERSION "${package_json_version}")
set(CPACK_PACKAGING_INSTALL_PREFIX "/var/www")
set(CPACK_RPM_PACKAGE_ARCHITECTURE "noarch")
set(CPACK_RPM_PACKAGE_RELOCATABLE OFF)
set(CPACK_RPM_PACKAGE_REQUIRES "nginx")

include(CPack)
