install(FILES ip_network_filter.py
        DESTINATION nemea_adict
        PERMISSIONS OWNER_EXECUTE OWNER_WRITE OWNER_READ
                         GROUP_EXECUTE GROUP_READ
                         WORLD_EXECUTE WORLD_READ
)
