# Datapoint aggregator

Nemea module to aggregate ADiCT datapoints in time.

Author: Jakub Magda <magda@cesnet.cz>

## Description
A module for ADiCT which aggregates incoming datapoints from input (JOSN format) and after given time sends it aggregated to output.
The module aggregates datapoints to one when all these attributes are the same:
- entity type
- entity ID
- attribute
- value

Value `t1` is set to minimum, value `t2` to maximum. Confidence `c` is set to maximum.
Source tags are aggregated as a string of all sources with `','` as delimiter.

The module works with 2 threads. First for receiving data and second for sending aggregated data. It means that no data leaks are possible due to blocked input. 

Datapoints with attributes of any data type can be aggregated, so it can be used for aggregation of output of any ADiCT input module.

### Parameters

- `-S --send-interval <seconds>` Set the interval of sending data to output interface (in seconds, default: 900).

**Common TRAP parameters**

- `-h [trap,1]` Print help message for this module / for libtrap specific parameters.
- `-i IFC_SPEC` Specification of interface types and their parameters (mandatory).
- `-v` Be verbose.

### NEMEA Interfaces (common to all modules)

- Inputs: 1 ( JSON format, type id "adict_datapoint" )
- Outputs: 1 ( JSON format, type id "adict_datapoint" )

### Examples
```
python3 dp_aggregator.py -S 300 -i u:output_from_recog,u:output_from_dpa
./dp_aggregator.py --send-interval 600  -i u:input,u:output
```
