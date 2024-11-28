#!/usr/bin/python3
"""
Analyze IP flows to get information about open ports on each IP address.
This information is periodically sent to ADiCT server.

The open ports are detected simply by observing successfully established
TCP connections, i.e. pairs of SYN and SYN+ACK packets.
When bi-flow are available, each bi-flow with non-zero packets in each direction
and both SYN and ACK flags set is used to mark the DST_PORT as open on DST_IP.
For uni-flows, the pairing is done in the module. ...

The module accepts a list of IP prefixes to monitor.
Only ports on those IP addresses are considered and sent to ADiCT.

----------------------------------------------------------------
Author: Josef Koumar <koumajos@fit.cvut.cz>
        Vaclav Bartos <bartos@cesnet.cz>

Copyright (C) 2022-2023 CESNET

LICENSE TERMS

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:
    1. Redistributions of source code must retain the above copyright notice,
       this list of conditions and the following disclaimer.
    2. Redistributions in binary form must reproduce the above copyright notice,
       this list of conditions and the following disclaimer in the documentation
       and/or other materials provided with the distribution.
    3. Neither the name of the Company nor the names of its contributors may be used
       to endorse or promote products derived from this software
       without specific prior written permission.

ALTERNATIVELY, provided that this notice is retained in full,
this product may be distributed under the terms of the GNU General Public License (GPL)
version 2 or later, in which case the provisions of the GPL apply INSTEAD OF those
given above.

This software is provided "as is", and any express or implied warranties, including,
but not limited to, the implied warranties of merchantability and fitness for
a particular purpose are disclaimed. In no event shall the company or contributors
be liable for any direct, indirect, incidental, special, exemplary, or consequential
damages (including, but not limited to, procurement of substitute goods or services;
loss of use, data, or profits; or business interruption) however caused and on any
theory of liability, whether in contract, strict liability, or tort (including
negligence or otherwise) arising in any way out of the use of this software,
even if advised of the possibility of such damage.
"""

# Standard libraries imports
import argparse
import re
import signal
import sys
import time
from argparse import FileType
from collections import namedtuple
from datetime import datetime
from functools import partial
from io import TextIOWrapper
from itertools import islice
from threading import Event, Lock, Thread
from typing import Callable, Iterable, Iterator, Optional

# NEMEA system library
import pytrap

# Third party imports
import requests

# Ignore global variable usage
# ruff: noqa: PLW0603

# output datapoint fields
TYPE = "ip"
ATTR = "open_ports"
HTTP_REQUEST_TIMEOUT = 10  # seconds
DATAPOINTS_PER_REQUEST = 500

# Global variables
# are bidirectional flows supported according to input unirec template?
biflow_support = None

found_open_ports = {}  # dict (ip,port)->(time_first,time_last,number_of_connections)
# data sending is done by a separate thread, lock is needed to avoid race conditions
found_open_ports_lock = Lock()

stop = Event()  # a flag to signalize the program should stop (stops the sending thread)

# A class (namedtuple) for simplified flow/biflow
Biflow = namedtuple(
    "Biflow", "srcip, srcport, dstip, dstport, time_first, time_last, tcp_flags"
)


def dbgprint(x):
    print(f"[{datetime.now().isoformat()}]", x, file=sys.stderr, flush=True)


def net_filter_true(ip):
    """Always return True, i.e. don't filter anything."""
    return True


def net_filter_networks(ip, networks_to_watch):
    """Return True if the given IP belongs to any of the monitored networks."""
    return any(ip in net for net in networks_to_watch)


net_filter = net_filter_true  # default filter function


# How does it work:
# For bi-flows with both sides filled (at least one packet in each direction):
#   If it's TCP and TCP_FLAGS contain both SYN and ACK (and not RST),
#   simply mark DST_PORT on DST_IP as open.
# For uni-directional flows:
#   We must try to pair both directions of the connection
#   (the two flows may come in any order, but should arrive soon after each other).
#   A temporary store (dict) is used to cache info about uni-dir flows:
#
#   - Search for reverse key [dst-src] in cache
#     - Found:
#       - The other direction was already observed, pair them together.
#       - Create a bi-flow, select the direction by comparing TIME_FIRST of the current
#         and cached flow.
#       - Continue as with bi-flow (apply IP and Port filters, if passed,
#         mark DST_PORT on DST_IP as open)
#       - Remove the record from the cache
#     - Not found:
#       - The other direction wasn't observed, yet. Store to cache.
#       - Store key [src-dst] to the cache, together with TIME_FIRST and TCP_FLAGS
#         (if this key was already there, overwrite it - a flow with the same key
#         shouldn't arrive short after the previous one, so it's probably an old record
#         for which we won't get the other direction anyway)
#
# Note that even if bi-flows are supported,
# some bidirectional communication can still be exported as two unidirectional flows.


class BiflowAggregator:
    def __init__(self):
        # map (srcip,srcport,dstip,dstport)->(time_first,time_last,tcp_flags)
        self._cache = {}
        # cache from previous time window
        # (used only to look up flows, new ones are written to _cache)
        self._prev_cache = {}

    def rotate_cache(self):
        """Clear the current cache (should be called every few minutes)"""
        # The current cache is backed up, and flows are always searched for in both
        # the current and the previous cache.

        # IMPORTANT: Although this is called from a separate thread, locking is not
        # necessary. Cache rotation can occur anywhere in process_flow() without any
        # unexpected consequences. JUST BE CAREFUL WITH ANY FUTURE MODIFICATIONS,
        # ALWAYS RE-THINK IF LOCKING IS STILL NOT NEEDED.
        self._prev_cache = self._cache
        self._cache = {}

    def cache_rotation_thread(self, interval: int):
        """Helper function to be run as a separate (daemon) thread, rotates cache
        every 'interval' seconds"""
        next_rotation_time = time.time() + interval
        while True:
            time.sleep(next_rotation_time - time.time())
            self.rotate_cache()
            next_rotation_time += interval

    def process_flow(self, rec: pytrap.UnirecTemplate) -> Optional[Biflow]:
        """Try to aggregate a flow with the corresponding cached one in the other
        direction, if any.

        Return the aggregated bi-flow or None.

        Returned bi-flow is a tuple: (
            srcip, srcport, dstip, dstport, time_first, time_last, tcp_flags
        )
        """
        srcip = rec.SRC_IP
        srcport = rec.SRC_PORT
        dstip = rec.DST_IP
        dstport = rec.DST_PORT
        time_first = rec.TIME_FIRST
        time_last = rec.TIME_LAST
        tcp_flags = rec.TCP_FLAGS
        # Look if the dst->src flow was already observed
        # (if it is there, we'll process it and won't need anymore - use pop())
        rev_key = (dstip, dstport, srcip, srcport)
        reverse_flow = self._cache.pop(rev_key, None) or self._prev_cache.pop(
            rev_key, None
        )
        if reverse_flow is not None:
            # The dst->src flow was already observed, pair them together into
            # a bidirectional flow
            c_time_first, c_time_last, c_tcp_flags = reverse_flow
            if time_first < c_time_first:
                # the current flow was first, its SRC IP initiated the connection,
                # so it's SRC of bidir flow
                aggregated_flow = Biflow(
                    srcip,
                    srcport,
                    dstip,
                    dstport,
                    min(time_first, c_time_first),
                    max(time_last, c_time_last),
                    tcp_flags | c_tcp_flags,
                )
            else:
                # the cached flow was first, reverse the IP addresses
                aggregated_flow = Biflow(
                    dstip,
                    dstport,
                    srcip,
                    srcport,
                    min(time_first, c_time_first),
                    max(time_last, c_time_last),
                    tcp_flags | c_tcp_flags,
                )
            return aggregated_flow
        else:
            # Corresponding flow in the other direction wasn't observed, yet - cache
            # this flow (If there already was a flow in the same direction, it's OK
            # to overwrite. Flows with the same key shouldn't arrive short after each
            # other, so it's probably just an old record for which we won't get the
            # other direction anyway.)
            fwd_key = (srcip, srcport, dstip, dstport)
            self._cache[fwd_key] = (time_first, time_last, tcp_flags)
            return None


def process_biflow(biflow: Biflow):
    """If biflow corresponds to a successful connection to the DST_IP/DST_PORT,
     mark it as open in 'found_open_ports' dictionary.

    It assumes there was at least one open packet observed in eac direction
    (single-direction flows were filtered out earlier).
    """
    if not net_filter(biflow.dstip):
        return

    # Port is open and matched both filters - add it to the dict
    # first search if this port already has a record in the dict
    key = (biflow.dstip, biflow.dstport)
    with found_open_ports_lock:
        rec = found_open_ports.get(key)
        if rec is None:
            # not there yet, add new record
            found_open_ports[key] = {
                "t1": biflow.time_first,
                "t2": biflow.time_last,
                "conns": 1,
            }
        else:
            # there already is a record with the same IP:port, update it
            rec["t1"] = min(rec["t1"], biflow.time_first)
            rec["t2"] = max(rec["t2"], biflow.time_last)
            rec["conns"] += 1


def batched(iterable: Iterable, n: int) -> Iterator[list]:
    """Batch data into tuples of length n. The last batch may be shorter."""
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while True:
        batch = list(islice(it, n))
        if not batch:
            break
        yield batch


def post_datapoint_list(url: str, datapoints: list):
    """Post datapoints to ADiCT server, handling possible errors."""
    if not datapoints:
        return

    for batch in batched(datapoints, DATAPOINTS_PER_REQUEST):
        try:
            resp = requests.post(
                url + "/datapoints",
                json=batch,
                timeout=HTTP_REQUEST_TIMEOUT,
            )
        except requests.ConnectionError as e:
            dbgprint(f"Send failed due to ConnectionError: {e}")
            continue
        except requests.Timeout:
            dbgprint("Send failed due to timeout.")
            continue

        if resp.status_code == 200:
            dbgprint(
                f"{len(batch)} datapoints successfully sent.",
            )
        else:
            dbgprint(
                f"Error when trying to send datapoints ({resp.status_code}): "
                f"{resp.text}",
            )


def send_datapoints(url: str, srctag: str):
    """Send data about open ports (in found_open_ports dict) as data-points.

    The found_open_ports dict is cleared after the data are send.

    If URL is not given, print basic info to stdout.

    Parameters
    -----------
    srctag : str
        Module name to fill as "src" key
    url : str
        The URL to ADiCT server.
    """
    global found_open_ports
    # Copy reference to the dict and replace it with a new one. A Lock is used to
    # wait until the main thread finishes writing into found_open_ports, if any.
    with found_open_ports_lock:
        to_send = found_open_ports
        found_open_ports = {}

    dbgprint("Sending open ports...")
    datapoints = []
    for key, val in to_send.items():
        ip, port = key
        t1 = (
            val["t1"].toDatetime().isoformat()
        )  # ISO format needed for ADiCT (YYYY-MM-DDThh:mm:ss[.fff][Z])
        t2 = val["t2"].toDatetime().isoformat()
        conns = val["conns"]

        if t2 < t1:  # shouldn't happen, but... just in case
            dbgprint(
                f"WARNING: time_last < time_first, this shouldn't be possible "
                f"(unless a flow with wrong timestamps was received)! "
                f"The record will be dropped. Details: "
                f"ip={ip}, port={port}, time_first={t1}, time_last={t2}",
            )
            continue

        datapoint = {
            "type": TYPE,
            "id": str(ip),
            "attr": ATTR,
            "v": port,
            "t1": t1,
            "t2": t2,
            "src": srctag,
        }
        if url:
            datapoints.append(datapoint)
        else:
            # just print, don't send anywhere
            print(f"{ip}:{port}  {t1} - {t2} ({conns}x)")

    if url:
        post_datapoint_list(url, datapoints)

    dbgprint("Done.")


def sender_thread_func(url: str, srctag: str, interval: int):
    """Sends out cached data about open ports every 'interval' seconds
    (to be run as a separate thread)

    url and src_tag parameters are passed to send_datapoints().
    """
    next_send_time = time.time()
    while not stop.is_set():
        # Sleep for the 'interval' seconds from the last interation
        next_send_time += interval
        sleep_time = next_send_time - time.time()
        # Check for the case sending is so slow
        # or blocked it takes longer than the interval
        if sleep_time < 0:
            dbgprint(
                "WARNING: The last attempt to send out data took longer than the send "
                "interval!",
            )
            # next_send_time is in the past,
            # increment it so many times it gets into the future
            next_send_time += (-sleep_time) // interval
            sleep_time = 0
        # Wait for sleep_time seconds, unless the "stop" flag is set,
        # in which case stop this thread.
        if stop.wait(sleep_time) is True:
            # Exit this thread. Any pending data will be sent by the main thread.
            return
        send_datapoints(url=url, srctag=srctag)


def create_network_filter(
    networks: Optional[Iterable[str]],
    networks_file: Optional[TextIOWrapper],
    verbose: Optional[bool] = False,
) -> Callable:
    """Load networks passed via arguments or a file, return filtering function"""

    def validate_ipv46_network(
        net_str: str, line_no: int = None
    ) -> pytrap.UnirecIPAddrRange:
        try:
            return pytrap.UnirecIPAddrRange(net_str)
        except ValueError as e:
            raise ValueError(
                "Invalid network"
                + (f" on line {line_no}" if line_no is not None else " passed")
                + f": {e}"
            ) from e

    # Load networks (IP prefixes) to watch
    networks_to_watch = set()
    if networks:
        for net_str in networks:
            networks_to_watch.add(validate_ipv46_network(net_str))

    if networks_file:
        for i, net_str in enumerate(networks_file, 1):
            net_str = re.sub(r"(#|//).*", "", net_str).strip()
            if net_str == "":
                continue
            networks_to_watch.add(validate_ipv46_network(net_str, i))

    # Create net_filter function
    # - return True if given IP belongs to any of the monitored networks
    if networks_to_watch:
        net_filter = partial(net_filter_networks, networks_to_watch=networks_to_watch)
        if verbose:
            dbgprint(
                "Only IPs from these networks will be watched for open ports:",
            )
            dbgprint(",".join(map(str, networks_to_watch)))
    else:
        net_filter = net_filter_true
    return net_filter


def signal_handler(sig, frame):
    # registered on SIGINT (Ctrl-C), SIGTERM, SIGABRT
    # Signalize to the sender thread and to the main loop to stop
    dbgprint("Signal received, going to exit...")
    stop.set()
    # Revert signal handlers to defaults, so the next Ctrl-C (or anoher signal) stops
    # the program immediately
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGABRT, signal.SIG_DFL)


def main():
    """Main function of the module."""
    global biflow_support, net_filter

    parser = argparse.ArgumentParser(
        description="Analyze IP flows to get information about open ports on each IP "
        "address. This information is periodically sent to ADiCT server.",
    )
    # Standard NEMEA module arguments
    parser.add_argument(
        "-i",
        metavar="IFC_SPEC",
        help="Specification of interface types and their parameters, "
        'see "-h trap" (mandatory parameter).',
    )
    parser.add_argument("-v", help="Be verbose.", action="store_true")
    parser.add_argument("-vv", help="Be more verbose.", action="store_true")
    parser.add_argument("-vvv", help="Be even more verbose.", action="store_true")

    # Custom arguments
    parser.add_argument(
        "-u",
        "--url",
        metavar="URL",
        help="Base URL of ADiCT API. If not given, results are just printed to stdout "
        "(for testing/debugging)",
    )
    parser.add_argument(
        "-S",
        "--send-interval",
        type=int,
        metavar="SECONDS",
        default=300,
        help="Period of sending data to ADiCT server (in seconds, default: 300)",
    )
    parser.add_argument(
        "-n",
        "--networks",
        nargs="+",
        metavar="IP_PREFIX",
        default="",
        help="IP networks (in CIDR format) to monitor. Only data of IPs from these "
        "networks will be included. Multiple networks can be specified as "
        '"-n 192.168.1.0/24 10.0.0.0/8". Both IPv4 and IPv6 is supported. '
        "If not set, all IPs are included.",
    )
    parser.add_argument(
        "-N",
        "--networks-file",
        metavar="IP_PREFIX_FILE",
        type=FileType("r"),
        help="Same as -n, but load list of prefixes from file "
        "(one prefix per line, '#' or '//' comments supported).",
    )
    parser.add_argument(
        "-t",
        "--srctag",
        metavar="NAME",
        default="open_ports",
        help="Name of this instance (used as 'src' tag in data-points sent to ADiCT). "
        "Default: open_ports",
    )
    parser.add_argument(
        "-r",
        "--cache-rotation",
        type=int,
        metavar="SECONDS",
        default=120,
        help="Period of cache rotation of the internal biflow aggregator. Should be "
        "larger than the maximum expected delay between receiving flow records "
        "of both directions of a connection (in seconds, default: 120)",
    )
    args = parser.parse_args()

    if args.cache_rotation < 1:
        print(
            "ERROR: Cache rotation interval must be at least 1 second", file=sys.stderr
        )
        return 1
    if args.send_interval < 1:
        print("ERROR: Send interval must be at least 1 second", file=sys.stderr)
        return 1

    # Parse networks and create a filter function
    try:
        net_filter = create_network_filter(
            args.networks, args.networks_file, verbose=True
        )
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    trap = pytrap.TrapCtx()
    trap.init(sys.argv, 1, 0)  # argv, ifcin - 1 input IFC, ifcout - 0 output IFC
    # Set timeout on the input interface to 500ms (so a signal is correctly handled
    # even if no data are being received)
    trap.ifcctl(ifcidx=0, dir_in=True, request=pytrap.CTL_TIMEOUT, value=500000)
    # Set the list of required fields in received messages.
    inputspec = (
        "ipaddr DST_IP,ipaddr SRC_IP,time TIME_FIRST,time TIME_LAST,uint32 PACKETS,"
        "uint16 DST_PORT,uint16 SRC_PORT,uint8 PROTOCOL,uint8 TCP_FLAGS"
    )
    trap.setRequiredFmt(0, pytrap.FMT_UNIREC, inputspec)
    rec = pytrap.UnirecTemplate(inputspec)

    biflow_aggregator = BiflowAggregator()

    if args.url:
        # Strip any trailing slash from the URL
        args.url = args.url.rstrip("/")

        # Test connection to the base URL
        # (try the '/' endpoint, it should return 200 OK)
        try:
            resp = requests.get(args.url + "/")
        except OSError as e:
            print(f"Test connection to ADiCT API failed: {e}")
            return 2
        if resp.status_code != 200:
            print(
                f"Test connection to ADiCT API failed, "
                f"unexpected reply ({resp.status_code}): {resp.text[:200]}"
            )
            return 2

    # Register the signal handler for correct program termination
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGABRT, signal_handler)

    # Start a separate thread for cache rotation in biflow_aggregator (make it a
    # daemon thread, so it's automatically joined/killed when the main thread exits)
    cache_rotation_thread = Thread(
        target=biflow_aggregator.cache_rotation_thread,
        args=(args.cache_rotation,),
        daemon=True,
    )
    cache_rotation_thread.start()

    # Start a separate thread for sending out data about found open ports
    sender_thread = Thread(
        target=sender_thread_func, args=(args.url, args.srctag, args.send_interval)
    )
    sender_thread.start()

    # Main loop to read ip-flows from input interface
    while not stop.is_set():
        # load IP flow from IFC interface
        try:
            data = trap.recv()
        except pytrap.FormatChanged as e:
            fmttype, inputspec = trap.getDataFmt(0)
            rec = pytrap.UnirecTemplate(inputspec)
            data = e.data
            biflow_support = None
        except pytrap.TimeoutError:
            continue
        if len(data) <= 1:
            stop.set()  # signalize to the sender thread to stop
            break
        rec.setData(data)  # set the IP flow to created template

        # Autodetect if bi-flow are supported
        if biflow_support is None:
            try:
                _ = rec.PACKETS_REV
                biflow_support = True
                dbgprint("Bi-flow support detected")
            except AttributeError:
                biflow_support = False
                dbgprint("Bi-flow support not detected")

        # === Process the (bi)flow ===

        # Input filters
        if rec.PROTOCOL != 6:  # TCP
            continue
            # TODO: Support detecting "open"/used UDP ports? (Not a problem
            #   here, but it must be supported by the target system (ADiCT))

        if rec.TCP_FLAGS & 0x12 != 0x12:  # require SYN & ACK flags
            # If there is no SYN flag, it's probably a continuation of a longer flow.
            # We can't use this, as in this case it's not possible to determine which
            # side initiated the connection from the flow timestamps. We also require
            # ACK flag, as each successfully opened TCP connection requires both SYN
            # and ACK flags in both directions.
            continue

        if not net_filter(rec.SRC_IP) and not net_filter(rec.DST_IP):
            # neither SRC_IP nor DST_IP belong to the set of monitored prefixes - skip
            continue

        # Detect if this flow is proper biflow (with both directions filled)
        if biflow_support and rec.PACKETS > 0 and rec.PACKETS_REV > 0:
            # it's biflow - parse needed information and detect open port
            biflow = Biflow(
                rec.SRC_IP,
                rec.SRC_PORT,
                rec.DST_IP,
                rec.DST_PORT,
                rec.TIME_FIRST,
                rec.TIME_LAST,
                rec.TCP_FLAGS,
            )
            process_biflow(biflow)
        else:
            # It's uniflow - try to aggregate it, if successful, detect open port
            biflow = biflow_aggregator.process_flow(rec)
            if biflow:
                process_biflow(biflow)

        # =========

    # Main loop stopped, wait for the sender thread to finish
    sender_thread.join()

    # Send any cached data before program exit
    if found_open_ports:
        send_datapoints(args.url, args.srctag)
    # Free allocated TRAP IFCs
    trap.finalize()


if __name__ == "__main__":
    main()
