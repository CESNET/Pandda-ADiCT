# The purpose of this file is to automatically determine install directories.
#
# If no directories are defined, use GNU install directories by default.
# However, in case of RPM build, install directories are typically passed
# to CMake as definitions that overwrites the default paths.

include(GNUInstallDirs)

set(INSTALL_DIR_BIN ${CMAKE_INSTALL_FULL_BINDIR})

if (DEFINED LIB_INSTALL_DIR)
	set(INSTALL_DIR_LIB ${LIB_INSTALL_DIR})
else()
	set(INSTALL_DIR_LIB ${CMAKE_INSTALL_FULL_LIBDIR})
endif()

if (DEFINED INCLUDE_INSTALL_DIR)
	set(INSTALL_DIR_INCLUDE ${INCLUDE_INSTALL_DIR})
else()
	set(INSTALL_DIR_INCLUDE ${CMAKE_INSTALL_FULL_INCLUDEDIR})
endif()

if (DEFINED SYSCONF_INSTALL_DIR)
	set(INSTALL_DIR_SYSCONF ${SYSCONF_INSTALL_DIR})
else()
	set(INSTALL_DIR_SYSCONF ${CMAKE_INSTALL_FULL_SYSCONFDIR})
endif()

if (DEFINED SHARE_INSTALL_PREFIX)
	set(INSTALL_DIR_SHARE ${SHARE_INSTALL_PREFIX})
else()
	set(INSTALL_DIR_SHARE ${CMAKE_INSTALL_FULL_DATAROOTDIR})
endif()

set(INSTALL_DIR_MAN "${INSTALL_DIR_SHARE}/man/")
set(INSTALL_DIR_DOC "${INSTALL_DIR_SHARE}/doc/${CMAKE_PROJECT_NAME}/")
