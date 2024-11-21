install(FILES ip_activity2.py
        DESTINATION ${INSTALL_DIR_BIN}/nemea_adict
        PERMISSIONS OWNER_EXECUTE OWNER_WRITE OWNER_READ
                         GROUP_EXECUTE GROUP_READ
                         WORLD_EXECUTE WORLD_READ
)
