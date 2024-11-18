add_subdirectory(dp_aggregator)
add_subdirectory(ip_activity2)
add_subdirectory(nemea_adict_sender)
add_subdirectory(open_ports)
add_subdirectory(recog)

install(FILES requirements.txt
        DESTINATION ${INSTALL_DIR_BIN}/nemea_adict
        PERMISSIONS OWNER_EXECUTE OWNER_WRITE OWNER_READ
                         GROUP_EXECUTE GROUP_READ
                         WORLD_EXECUTE WORLD_READ
)
