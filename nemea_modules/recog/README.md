# Recog

Input module to analyze ssh and smtp banners.

Author: Jakub Magda <magda@cesnet.cz>

## Description
Module for ADiCT which recognizes the Operating System service and hardware of a source IP address from a flow record (IDP_CONTENT_REV) and by given recog xml database.
Patterns from database in form of regular expressions are matched with incoming flow. After match information about OS service or hardware are send as message in JSON format to ADiCT server.

### Recog fingerprints
Module use for detection of flow xml databases of fingerprints from open source project recog by rapid7. Modul can use 2 databases `ssh_banners.xml` and `smtp_banners.xml`.
Each fingerprint contains pattern which is regular expression that is used to match banners and information about IP address that use that pattern as operating system service or hardware.
### Output Datapoint
Modul output is in ADiCT datapoint format that contains these information: destination IP, time, attribute (which is `recog_ssh` or `recog_smtp`),
source of information and most important value - information obtained by modul. Information is structured as a dictionary containing multiple nested dictionaries.
Each nested dictionary represents a specific aspect of the system. There are 5 major keys `os`, `service`, `hw`, `openssh` and `host`, that represent categories of information (names of nested dictionaries).
`openssh` dictionary are specific for ssh banners and provides OpenSSH comment, while `host` is specific for smtp banners.
Example of structure of value part of datapoint:
```
{
    "os": {
        "vendor": "Raspbian",
        "family": "Linux",
        "product": "Linux",
        "version": "10.0"
    },
    "service": {
        "version": "7.9p1",
        "vendor": "OpenBSD",
        "family": "OpenSSH",
        "product": "OpenSSH",
        "cpe23": "cpe:/a:openbsd:openssh:7.9p1"
    },
    "hw": {
        "product": "Raspberry Pi"
    },
    "openssh": {
        "comment": "Raspbian-10+deb10u2+rpt1"
    }
}
```

### Parameters

- `-d [database_file_path]` Path to database with which modul will match incoming flow data.
- `-m [ssh/smtp]` Set mode of module, which flow data will be analysed. (still has to be given right database)

**Common TRAP parameters**

- `-h [trap,1]` Print help message for this module / for libtrap specific parameters.
- `-i IFC_SPEC` Specification of interface types and their parameters (mandatory).
- `-v` Be verbose.

### NEMEA Interfaces (common to all modules)

- Inputs: 1 ( Required Unirec Fields: `ipaddr DST_IP, bytes IDP_CONTENT_REV, time TIME_FIRST, time TIME_LAST`)
- Outputs: 1 ( JSON format - data-points sent via Unirec message to nemea_adict_sender and then to ADiCT server )

### Examples
```
python3 recog -d ./ssh_banners.xml -m ssh -i u:ssh_flow_for_example,u:out_to_nemea_adict_sender
./recog -d ./ssh_banners.xml -m ssh -i p:8001,u:out_to_nemea_adict_sender
python3 recog -d ./smtp_banners.xml -m smtp -i u:smtp_flow_for_example,u:out
./recog -d ./smtp_banners.xml -m smtp -i p:8002,u:output

```
