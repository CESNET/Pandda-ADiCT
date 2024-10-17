# Nemea ADiCT sender

NEMEA module to send data-points to ADiCT server.

Module recieves JSON via TRAP interface and send it to desired URL. If no URL is provided, data are printed to stdout.


## Interfaces
- Inputs: 1 ( `Required JSON format` )  
- Outputs: 0 

## Parameters
-  `-u  --url <string>`        URL of ADiCT server (print data-points to stdout if not specified)
-  `-s  --src <sring>`         Name of this data source (add or overwrite the 'src' field in datapoints sent)
-  `-I  --indent <number> `    When writing to stdout, pretty-print JSON with indentation set to N spaces.

### Common TRAP parameters
- `-h [trap,1]`      Print help message for this module / for libtrap specific parameters.
- `-i IFC_SPEC`      Specification of interface types and their parameters (mandatory).
- `-v`               Be verbose.
- `-vv`              Be more verbose.
- `-vvv`             Be even more verbose.

