# Open ports

## Description
Input module for ADiCT. It detects open ports on monitored IP addresses by observing successfully established TCP
connections in flow data. 

Both unidirectional and bidirectional flows are supported on input. Uni-flows are first aggregated into bi-flows
(see Bi-flow aggregation section below).

Each bidirectional TCP flow (with SYN+ACK) is considered a successfully established TCP connection, which means the
destination port in opened on the destination address. If the address belongs to the specified network(s)
(by `-n` or `-N` parameter), this information is stored as a tuple (IP, port, time_first, time_last).
Every 5 minutes (or another interval given by the `--send-interval` parameter) all these tuples are sent to ADiCT
as a set of data-points.

It is recommended to specify the IP addresses to watch by `-n` or `-N` parameter. Otherwise, it will report open ports
on not only "your" IP addresses, but also the external ones.

TODO: Add a possibility to limit the range of ports to watch.

## Parameters

    usage: open_ports.py [-h] [-i IFC_SPEC] [-v] [-vv] [-vvv] [-u URL]
                         [-S SECONDS] [-n IP_PREFIX [IP_PREFIX ...]]
                         [-N IP_PREFIX_FILE] [-t NAME] [-r SECONDS]

    optional arguments:
      -h, --help            show this help message and exit
      -i IFC_SPEC           Specification of interface types and their parameters,
                            see "-h trap" (mandatory parameter).
      -v                    Be verbose.
      -vv                   Be more verbose.
      -vvv                  Be even more verbose.
      -u URL, --url URL     Base URL of ADiCT API. If not given, results are just
                            printed to stdout (for testing/debugging)
      -S SECONDS, --send-interval SECONDS
                            Period of sending data to ADiCT server (in seconds,
                            default: 300)
      -n IP_PREFIX [IP_PREFIX ...], --networks IP_PREFIX [IP_PREFIX ...]
                            IP networks (in CIDR format) to monitor. Only data of
                            IPs from these networks will be included. Multiple
                            networks can be specified as "-n 192.168.1.0/24
                            10.0.0.0/8". Both IPv4 and IPv6 is supported. If not
                            set, all IPs are included.
      -N IP_PREFIX_FILE, --networks-file IP_PREFIX_FILE
                            Same as -n, but load list of prefixes from file (one
                            prefix per line, '#' or '//' comments supported).
      -t NAME, --srctag NAME
                            Name of this instance (used as 'src' tag in data-
                            points sent to ADiCT). Default: open_ports
      -r SECONDS, --cache-rotation SECONDS
                            Period of cache rotation of the internal biflow
                            aggregator. Should be larger than the maximum expected
                            delay between receiving flow records of both
                            directions of a connection (in seconds, default: 120)

## Input

Requires UniRec input with the following fields:

    ipaddr DST_IP,ipaddr SRC_IP,time TIME_FIRST,time TIME_LAST,uint32 PACKETS,uint16 DST_PORT,uint16 SRC_PORT,uint8 PROTOCOL,uint8 TCP_FLAGS

Bidirectional flows are supported - they are automatically recognized by presence of the PACKETS_REV field.


## Output

ADiCT formatted datapoints, one for each open port (`IP:port` combination).
If `--url` is passed, data are send to ADiCT API (`/datapoints` endpoint; in batches of 500 datapoints at maximum),
otherwise datapoints are just printed to standard output.

Datapoint format:

    {
        'type': 'ip',
        'id': <ip address>,
        'attr': 'open_ports',
        'v': <port>,
        't1': <timestamp of the first packet>,
        't2': <timestamp of the last packet>,
        'src': <tag>
    }

`t1` is the minimum of `TIME_FIRST` fields over all flows using this `IP:port` observed within the send interval.
Analogously `t2` and `TIME_LAST`.

### Bi-flow aggregation

The module contains an internal bi-flow aggregator - unidirectional flows are aggregated into bidirectional ones.
Even if input already supports bi-flows, those with just one direction filled are still send to the aggregator
(since even if exporters send biflows, there might be pairs of matching unidirectional flows, e.g. because each 
direction goes through a different probe). Biflows with packets in both directions are directly evaluated without
aggregation.

The direction of the flow is determined by time of the first packet in each flow (TIME_FIRST field) (only TCP flows
with SYN and ACK flags in both directions are considered, i.e. containing the beginning of a connection; other flows
are dropped at input).

How it works:
There is a cache of unidirectional flows. For each incoming flow, a matching flow in the other direction is first
looked up in the cache. If found - the two flows are merged into a bi-flow and sent for further processing.
Otherwise, the current flow is stored to the cache.

The cache needs to be emptied after some time - it's periodically wiped out (every 2 minutes by default), but a copy
of the old one is kept for one more interval and each incoming flow is looked up in this old cache as well.
In other words, there are actually two caches. New flows are stored into the 'current' one, but searched in both the
'current' one and the 'old' one. Every interval, the 'current' one is moved to be the 'old' one and a new empty
'current' cache is created.
This way, there is always a history of 2-4 minutes of flows available to search for the matching flow.

