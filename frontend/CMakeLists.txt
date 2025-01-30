cmake_minimum_required(VERSION 3.12)

project(pandda_gui DESCRIPTION "User interface for PANDDA project")

add_custom_target(gui ALL COMMAND npm install && npm run build)
install(DIRECTORY "${PROJECT_SOURCE_DIR}/dist/" DESTINATION ".")

# Ensure presence of version specifier
if(NOT DEFINED package_version)
    message(FATAL_ERROR "Variable `package_version` is not set!")
endif()

# CPack configuration for RPM packaging
set(CPACK_GENERATOR "RPM")
set(CPACK_PACKAGE_CONTACT "Dávid Benko <benko@cesnet.cz>")
set(CPACK_PACKAGE_NAME pandda_gui)
set(CPACK_PACKAGE_RELEASE 1)
set(CPACK_PACKAGE_VENDOR "CESNET z.s.p.o.")
set(CPACK_PACKAGE_VERSION "${package_version}")
set(CPACK_PACKAGING_INSTALL_PREFIX "/var/www")
set(CPACK_RPM_PACKAGE_ARCHITECTURE "noarch")
set(CPACK_RPM_PACKAGE_RELOCATABLE OFF)
set(CPACK_RPM_PACKAGE_REQUIRES "pandda_adict == ${package_version}, nginx")

include(CPack)
