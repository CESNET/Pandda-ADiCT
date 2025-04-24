#!/usr/bin/env python3

"""
Count number of flows, packets and bytes sent and received by each IP address
(in specified networks) per configurable time interval.
This variant uses bidirectional flows and counts both outgoing and incoming
traffic (so even an inactive address, such as a device turned off, can exhibit
some (incoming) activity, e.g. because of scans).
"""

import signal
import sys
import threading
from argparse import ArgumentParser
from datetime import datetime, timedelta
from json import dumps
from pathlib import Path
from queue import Queue
from sys import argv, stderr

import pytrap

sys.path.insert(0, str(Path(__file__).parent.parent / "common"))
from ip_network_filter import IPNetworks

inputspec = (
    "ipaddr DST_IP,ipaddr SRC_IP,uint64 BYTES,time TIME_FIRST,"
    "time TIME_LAST,uint32 PACKETS"
)

verbose = False
stop = False  # global flag to stop reading


class TrapIfc:
    """Class wrapping the PyTrap functionality."""

    def __init__(self, input_spec):
        """Initialize PyTrap interface for receiving data in UNIREC format."""
        self.input_spec = input_spec
        self.trap = pytrap.TrapCtx()
        self.rec = pytrap.UnirecTemplate(input_spec)

        try:
            self.trap.init(argv, 1, 1)
        except pytrap.TrapError as e:
            print(f"PyTrap: {e}", file=stderr)
            sys.exit(1)
        except pytrap.TrapHelp:
            sys.exit(0)

        self.trap.setRequiredFmt(0, pytrap.FMT_UNIREC, input_spec)
        self.trap.setDataFmt(0, pytrap.FMT_JSON)

    def recv_data(self):
        """Attempt to read data from trap interface.

        Returns:
            True on success, False otherwise."""
        try:
            self.data = self.trap.recv()
            return self.set_rec_if_data()
        except pytrap.FormatChanged as e:
            return self.handle_format_change_exception(e)
        except pytrap.FormatMismatch as e:
            print(e, file=stderr)
            return False

    def send_data(self, data):
        """Attempt to send data by trap interface."""
        try:
            self.trap.send(data)
        except pytrap.TimeoutError as e:
            print(e, file=stderr)
        except pytrap.TrapError as e:
            print(e, file=stderr)
        except pytrap.Terminated as e:
            print(e, file=stderr)
            raise
        except Exception:
            print("Unexpected error during trap.send", file=stderr)
            raise

    def return_time(self, option):
        if option == "TIME_FIRST":
            return self.rec.TIME_FIRST.toDatetime()
        elif option == "TIME_LAST":
            return self.rec.TIME_LAST.toDatetime()

    def return_src_ip(self):
        return self.rec.SRC_IP

    def return_dst_ip(self):
        return self.rec.DST_IP

    def return_bytes(self):
        return self.rec.BYTES

    def return_bytes_rev(self):
        return self.rec.BYTES_REV

    def return_packets(self):
        return self.rec.PACKETS

    def return_packets_rev(self):
        return self.rec.PACKETS_REV

    def set_rec_if_data(self):
        if len(self.data) <= 1:
            return False
        self.rec.setData(self.data)
        return True

    def handle_format_change_exception(self, e):
        _fmttype, self.input_spec = self.trap.getDataFmt(0)
        self.rec = pytrap.UnirecTemplate(self.input_spec)
        self.data = e.data
        return self.set_rec_if_data()

    def __del__(self):
        self.trap.finalize()


def floor_time(tm: datetime, interval: int):
    """Return interval beginning closest to the given time"""
    return tm - timedelta(seconds=(tm.timestamp() % interval))


def slot_generator(tm: datetime, interval: int):
    while True:
        tm = tm + timedelta(seconds=interval)
        if verbose:
            next_tm = tm + timedelta(seconds=interval)
            print(f"Creating slot from {tm:%H:%M:%S} to {next_tm:%H:%M:%S}")
        yield tm


def flow_split(start, end, interval):
    """Dividing one flow  into coverage of the share, per one time period,
    based on count of time periods in which interval lasts."""

    count = 0
    while start < end:
        start += timedelta(seconds=interval)
        count += 1
    return 1 / count


def _ip_filtering(networks: IPNetworks, ip: pytrap.UnirecIPAddr):
    """
    Check if record for current ip should be stored based on monitored prefixes.
    If no prefixes are set, all ip addresses should be stored.
    """
    return not networks.networks or ip in networks


def _insert_flow(  # noqa PLR0913
    data_table,
    slot,
    ip,
    in_bytes,
    in_packets,
    in_flow_fraction,
    out_bytes,
    out_packets,
    out_flow_fraction,
):
    """
    Increment counters in data table with given values of a flow record

    data_table: main data table
    slot: time slot (datetime of the beginning of the slot)
    ip: ip address whose counters to increment
    in_bytes: number of incoming bytes
    in_packets: number of incoming packets
    in_flow_fraction: fraction of the flow that is in the slot (only used when
        a flow spans multiple slots, otherwise 1)
    out_bytes: number of outgoing bytes
    out_packets: number of outgoing packets
    out_flow_fraction: fraction of the flow that is in the slot (only used when
        a flow spans multiple slots, otherwise 1)
    """

    # only increment the number of flows if some data went in that direction
    # (when bi-dir flows are used, one direction can be empty/zeros)
    in_flows = in_flow_fraction if in_packets > 0 else 0
    out_flows = out_flow_fraction if out_packets > 0 else 0

    if ip in data_table[slot]:
        data_table[slot][ip]["in_bytes"] += in_bytes
        data_table[slot][ip]["in_packets"] += in_packets
        data_table[slot][ip]["in_flows"] += in_flows
        data_table[slot][ip]["out_bytes"] += out_bytes
        data_table[slot][ip]["out_packets"] += out_packets
        data_table[slot][ip]["out_flows"] += out_flows
    else:
        data_table[slot][ip] = {
            "in_bytes": in_bytes,
            "in_packets": in_packets,
            "in_flows": in_flows,
            "out_bytes": out_bytes,
            "out_packets": out_packets,
            "out_flows": out_flows,
        }


def data_aggregation(
    data_table: dict, interval: int, trap, networks: IPNetworks, biflow: bool
):
    """Aggregate incoming flow records into an appropriate time period in
    timeline. If record lasted throughout multiple time periods, it is divided
    and values are interpolated into multiple smaller records, which are then
    counted to corresponding time periods."""

    src_ip = trap.return_src_ip()
    dst_ip = trap.return_dst_ip()
    src_filter = _ip_filtering(
        networks, src_ip
    )  # true if src_ip belong to one of selected networks
    dst_filter = _ip_filtering(networks, dst_ip)

    if not (src_filter or dst_filter):
        return

    bytes = trap.return_bytes()
    packets = trap.return_packets()
    if biflow:
        bytes_rev = trap.return_bytes_rev()
        packets_rev = trap.return_packets_rev()
    else:
        bytes_rev = 0
        packets_rev = 0

    flow_start = trap.return_time("TIME_FIRST")
    flow_end = trap.return_time("TIME_LAST")
    slot = floor_time(flow_start, interval)  # time of beginning of this slot/interval

    if flow_end - slot > timedelta(seconds=interval):
        # Flow spans multiple time intervals
        # Divide it to multiple bins proportionally
        flow_duration = (flow_end - flow_start).total_seconds()

        while flow_end - slot > timedelta(seconds=0):
            interval_end = slot + timedelta(seconds=interval)
            interval_end = min(interval_end, flow_end)

            if slot not in data_table:
                # needed slot not in the table (anymore), put data into the oldest one
                oldest_slot = sorted(data_table.keys())[0]
                print(
                    f"Warning: Encountered a flow belonging to slot {slot} "
                    f"which was already sent out (current time: {current_time}). "
                    f"Adding it to the oldest available slot ({oldest_slot}). "
                    "The '--maxage' parameter needs to be increased!",
                    file=sys.stderr,
                )
                slot = oldest_slot

            duration = (
                interval_end - flow_start
            ).total_seconds()  # number of seconds in this slot
            frac = duration / flow_duration  # fraction of the flow in this slot

            if src_filter:
                # increment counters for SRC_IP of this flow
                # (incoming = BYTES_REV, outgoing = BYTES)
                _insert_flow(
                    data_table,
                    slot,
                    src_ip,
                    frac * bytes_rev,
                    frac * packets_rev,
                    frac,
                    frac * bytes,
                    frac * packets,
                    frac,
                )

            if dst_filter:
                # increment counters for DST_IP of this flow
                # (incoming = BYTES, outgoing = BYTES_REV)
                _insert_flow(
                    data_table,
                    slot,
                    dst_ip,
                    frac * bytes,
                    frac * packets,
                    frac,
                    frac * bytes_rev,
                    frac * packets_rev,
                    frac,
                )

            flow_start = interval_end
            slot = interval_end

    else:
        # flow lies in a single interval - simply increment counters
        if slot not in data_table:
            # needed slot not in the table (anymore), put data into the oldest one
            oldest_slot = sorted(data_table.keys())[0]
            if not insufficient_maxage_warning_printed:
                print(
                    f"Warning: Encountered a flow belonging to slot {slot} "
                    f"which was already sent out (current time: {current_time}). "
                    f"Adding it to the oldest available slot ({oldest_slot}). "
                    "The '--maxage' parameter needs to be increased!",
                    file=sys.stderr,
                )
            slot = oldest_slot

        if src_filter:
            # increment counters for SRC_IP of this flow
            # (incoming = BYTES_REV, outgoing = BYTES)
            _insert_flow(
                data_table, slot, src_ip, bytes_rev, packets_rev, 1, bytes, packets, 1
            )

        if dst_filter:
            # increment counters for DST_IP of this flow
            # (incoming = BYTES, outgoing = BYTES_REV)
            _insert_flow(
                data_table, slot, dst_ip, bytes, packets, 1, bytes_rev, packets_rev, 1
            )


def _post_data(trap, interval, queue, src_tag):
    """Send data to the trap interface based on queue
    of old intervals from input-processing method"""

    while True:
        queue_item = queue.get(block=True)  # get timestamp of interval to send
        if queue_item == "END":
            queue.task_done()
            break

        time, slot_data = queue_item
        t_start = time.isoformat()
        t_end = (time + timedelta(seconds=interval)).isoformat()
        if verbose:
            print(f"Sending data of slot {time:%H:%M:%S} ({len(slot_data)} IPs)")
        for ip, vals in slot_data.items():
            data = [
                {
                    "type": "ip",
                    "attr": "activity",
                    "id": str(ip),
                    "t1": t_start,
                    "t2": t_end,
                    "v": {
                        # Each value must be wrapped in a list, because this is
                        # an attribute of "time-series" type. As such, the value
                        # is expected to contain lists of numbers (one per each
                        # time slot). Even though we only send one value for
                        # each series, is still needs to be a list.
                        "in_flows": [float(round(vals["in_flows"], 4))],
                        "in_packets": [float(round(vals["in_packets"], 4))],
                        "in_bytes": [float(round(vals["in_bytes"], 4))],
                        "out_flows": [float(round(vals["out_flows"], 4))],
                        "out_packets": [float(round(vals["out_packets"], 4))],
                        "out_bytes": [float(round(vals["out_bytes"], 4))],
                    },
                    "src": src_tag,
                }
            ]

            trap.send_data(bytearray(dumps(data), "utf-8"))

        if verbose:
            print(f"Slot {time:%H:%M:%S} sent.")

        queue.task_done()


def stop_program(signum, frame):
    global stop  # noqa PLW0603
    stop = True
    # Reset signal handlers to default, so second signal closes
    # the program immediately
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGABRT, signal.SIG_DFL)
    if verbose:
        print(
            "Signal received. "
            "Going to stop the program after the cached data are sent. "
            "Press Ctrl-C again to exit immediately."
        )


def input_processing(trap: TrapIfc, interval, src_tag, maxage, networks: IPNetworks):
    """Main loop for receiving and processing data.

    time: depends on interval that user set. If user set for example --interval 600,
    this parameter will have values like this 10:00:00, 10:10:00, 10:20:00.
    This timestamps means start of intervals in which records are aggregated.

    ip: ip addresses for which are data stored in current interval
    """
    global current_time, insufficient_maxage_warning_printed  # noqa PLW0603

    # data_table = main data structure containing counters of flows/packets/bytes
    # for each time slot and IP address
    # Format of data table is: {time -> {ip -> {in/out_flows/packets/bytes}}}
    #   dict items: 'in_flows', 'in_packets', 'in_bytes',
    #               'out_flows', 'out_packets', 'out_bytes'
    data_table = {}

    # current time = the maximum of all flow_end timestamps seen
    current_time = None

    # biflow = support for biflow data
    biflow = None

    # a flag to prevent printing multiple warnings in a single time interval
    insufficient_maxage_warning_printed = False

    # queue for time slots which are to be sent
    #   contains tuples: (time_start, {ip -> {"flows"/"packets"/"bytes" -> value}})
    queue = Queue(maxsize=5)

    # create a separate thread for sending data
    t1 = threading.Thread(target=_post_data, args=(trap, interval, queue, src_tag))
    t1.start()

    # Register signal handler on common stopping signals - it sets "stop" to True
    signal.signal(signal.SIGINT, stop_program)
    signal.signal(signal.SIGTERM, stop_program)
    signal.signal(signal.SIGABRT, stop_program)

    while not stop:
        if not trap.recv_data():
            break
        if current_time is None:
            current_time = trap.return_time("TIME_LAST")
            slot = floor_time(current_time - timedelta(seconds=maxage), interval)
            data_table[slot] = {}
            generator = slot_generator(slot, interval)
        elif current_time < trap.return_time("TIME_LAST"):
            current_time = trap.return_time("TIME_LAST")
            # If some interval is older than max age, add it to the queue for send
            for time in sorted(data_table.keys()):
                if current_time - time > timedelta(seconds=maxage):
                    queue.put((time, data_table[time]), block=True)
                    data_table.pop(time)

        while slot < current_time:
            slot = next(generator)
            data_table[slot] = {}

            # reset flag, so the warning can be printed again
            # in the next slot if needed
            insufficient_maxage_warning_printed = False

        if biflow is None:
            try:
                _packets = trap.return_packets_rev()
                biflow = True
            except AttributeError:
                biflow = False

        data_aggregation(data_table, interval, trap, networks, biflow)

    # receive finished, put everything in the queue to send
    for time in sorted(data_table.keys()):
        queue.put((time, data_table[time]), block=True)

    # signal for thread to end
    queue.put("END", block=True)
    t1.join()

    if verbose:
        print("Finished.")


def replace_traphelp_in_argv(args):
    if args.traphelp:
        argv.remove("--traphelp")
        argv.extend(["-h", "trap"])


def parse_arguments():
    parser = ArgumentParser(
        description="ADiCT input module. Collect input flows, aggregate and "
        "send them as IP Activity intervals to the trap interface. It counts "
        "number of flows, packets and bytes sent and received by IP address "
        "in each interval. JSON formatted datapoints are sent to output Trap "
        "IFC."
    )

    parser.add_argument(
        "--traphelp", help="display help for Trap IFC", action="store_true"
    )

    parser.add_argument(
        "-i",
        help=(
            "specification of interface types and their parameters, see "
            '"--traphelp" (mandatory parameter)'
        ),
        type=str,
        metavar="IFC_SPEC",
    )

    parser.add_argument(
        "--interval",
        "-I",
        help=(
            "Length of one time interval, in which flow records will be aggregated, "
            "in seconds. (default: 10 min)."
        ),
        type=int,
        default=600,
        metavar="SECONDS",
    )

    parser.add_argument(
        "-m",
        "--maxage",
        help=(
            "Max possible age of incoming data (in seconds). Data of time "
            "intervals older than this are sent and deleted (default: 20min)."
        ),
        type=int,
        default=1200,
        metavar="SECONDS",
    )

    parser.add_argument(
        "-s", help="Source tag", type=str, default="", metavar="SRC_TAG"
    )

    parser.add_argument(
        "-n",
        "--networks",
        help="IP networks (in CIDR format) to monitor. Only data of IPs from "
        "these networks will be included. Multiple networks can be separated by "
        "commas or spaces (quote the whole list in that case). "
        "If not set, all IPs are included.",
        type=str,
        metavar="IPs",
        default="",
    )

    parser.add_argument(
        "-N",
        "--networks-file",
        help="Same as -n, but load list of prefixes from file "
        "(one prefix per line, '#' or '//' comments supported).",
        type=str,
        metavar="FILE",
        default="",
    )

    parser.add_argument("-v", "--verbose", help="Verbose mode", action="store_true")

    arg = parser.parse_args()

    if arg.maxage < arg.interval:
        print("Max data age can't be less than interval length.")
        sys.exit(1)

    return arg


def main(inputspec):
    global verbose  # noqa PLW0603
    args = parse_arguments()
    replace_traphelp_in_argv(args)
    trap = TrapIfc(inputspec)

    verbose = args.verbose  # set global verbose flag

    networks = IPNetworks()
    if args.networks:
        networks = IPNetworks.from_list(args.networks.replace(",", " ").split())
    elif args.networks_file:
        networks = IPNetworks.from_file(args.networks_file)

    if verbose:
        print("Watching IPs from networks:", ", ".join(map(str, networks.networks)))

    input_processing(trap, args.interval, args.s, args.maxage, networks)


if __name__ == "__main__":
    main(inputspec)
