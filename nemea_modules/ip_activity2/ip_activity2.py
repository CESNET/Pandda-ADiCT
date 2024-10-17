#!/usr/bin/env python3

import sys
import pytrap
import threading
import ipaddress
import signal
from json import dumps
from queue import Queue
from sys import stderr, argv
from argparse import ArgumentParser
from datetime import datetime, timedelta

inputspec = 'ipaddr SRC_IP,uint64 BYTES,time TIME_FIRST,time TIME_LAST,uint32 PACKETS'

verbose = False
stop = False  # global flag to stop reading


class TrapIfc:
    """ Class wrapping the PyTrap functionality. """

    def __init__(self, input_spec):

        """ Initialize PyTrap interface for receiving data in UNIREC format. """
        self.input_spec = input_spec
        self.trap = pytrap.TrapCtx()
        self.rec = pytrap.UnirecTemplate(input_spec)

        try:
            self.trap.init(argv, 1, 1)
        except pytrap.TrapError as e:
            print(f'PyTrap: {e}', file=stderr)
            exit(1)
        except pytrap.TrapHelp:
            exit(0)

        self.trap.setRequiredFmt(0, pytrap.FMT_UNIREC, input_spec)
        self.trap.setDataFmt(0, pytrap.FMT_JSON)

    def recv_data(self):
        """ Attempt to read data from trap interface.

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
        """ Attempt to send data by trap interface."""
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
        return str(self.rec.SRC_IP)

    def return_dst_ip(self):
        return str(self.rec.DST_IP)

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
            print(f"Creating slot from {tm:%H:%M:%S} to {tm+timedelta(seconds=interval):%H:%M:%S}")
        yield tm


def flow_split(start, end, interval):
    """Dividing one flow  into coverage of the share, per one time period,
       based on count of time periods in which interval lasts."""

    count = 0
    while start < end:
        start += timedelta(seconds=interval)
        count += 1
    return 1 / count


def _ip_filtering(networks, ip):
    """Check if record for current ip should be stored based on -N argument.
       If -N is not set, all ip addresses should be stored."""

    if networks == list():
        return True
    else:
        ip = int(ipaddress.ip_address(ip))
        for netw, mask in networks:
            if (ip & mask) == netw:
                return True

    return False


def _insert_data(data_table, slot, ip, rec_bytes, rec_packets, rec_flow):
    """Store one record in data table with given values."""

    if ip in data_table[slot]:
        data_table[slot][ip]["bytes"] += rec_bytes
        data_table[slot][ip]["packets"] += rec_packets
        data_table[slot][ip]["flows"] += rec_flow
    else:
        data_table[slot][ip] = {"bytes": rec_bytes,
                                "packets": rec_packets,
                                "flows": rec_flow}


def data_aggregation(data_table: dict, interval: int, trap, networks, biflow):
    """Aggregate incoming flow records into an appropriate time period in timeline.
       If record lasted throughout multiple time periods, it is divided and values are
       interpolated into multiple smaller records, which are then counted to corresponding
       time periods."""

    src_ip = trap.return_src_ip()
    src_filter = _ip_filtering(networks, src_ip)

    if biflow:
        dst_ip = trap.return_dst_ip()
        dst_filter = _ip_filtering(networks, dst_ip)
    else:
        dst_filter = False

    if src_filter or dst_filter:

        slot = floor_time(trap.return_time("TIME_FIRST"), interval)
        end = trap.return_time("TIME_LAST")

        if end - slot > timedelta(seconds=interval):
            # Flow spans multiple time intervals - divide it to multiple bins proportionally
            start = trap.return_time("TIME_FIRST")
            flow_duration = (end - start).total_seconds()
            flow_share = flow_split(slot, end, interval)
            bytes_per_sec = trap.return_bytes() / flow_duration
            packets_per_sec = trap.return_packets() / flow_duration
            if dst_filter:
                rev_bytes_per_sec = trap.return_bytes_rev() / flow_duration
                rev_packets_per_sec = trap.return_packets_rev() / flow_duration

            while end - slot > timedelta(seconds=0):
                interval_end = slot + timedelta(seconds=interval)
                if interval_end > end:
                    interval_end = end

                if slot not in data_table:
                    slot = list(sorted(data_table.keys()))[0]

                duration = (interval_end - start).total_seconds()
                if src_filter:
                    _insert_data(data_table, slot, src_ip, bytes_per_sec * duration, packets_per_sec * duration,
                                 flow_share)

                if dst_filter:
                    _insert_data(data_table, slot, dst_ip, rev_bytes_per_sec * duration, rev_packets_per_sec * duration,
                                 flow_share)

                start = interval_end
                slot = interval_end

        else:
            if slot not in data_table:
                slot = list(sorted(data_table.keys()))[0]

            if src_filter:
                _insert_data(data_table, slot, src_ip, trap.return_bytes(), trap.return_packets(), 1)

            if dst_filter:
                _insert_data(data_table, slot, dst_ip, trap.return_bytes_rev(), trap.return_packets_rev(), 1)


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
            data = [{
                "type": "ip",
                "attr": "activity",
                "id": ip,
                "t1": t_start,
                "t2": t_end,
                "v": {
                    "flows": [float(round(vals["flows"], 4))],
                    "packets": [float(round(vals["packets"], 4))],
                    "bytes": [float(round(vals["bytes"], 4))]
                },
                "src": src_tag
            }]

            trap.send_data(bytearray(dumps(data), 'utf-8'))

        if verbose:
            print(f"Slot {time:%H:%M:%S} sent.")

        queue.task_done()


def stop_program(signum, frame):
    global stop
    stop = True
    # Reset signal handlers to default, so second signal closes the program immediately
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGABRT, signal.SIG_DFL)
    if verbose:
        print("Signal received. Going to stop the program after the cached data are sent. Press Ctrl-C again to exit immediately.")


def input_processing(trap: TrapIfc, interval, src_tag, maxage, networks):
    """Main loop for receiving and processing data.
       Dictionary data_table is main data structure for storing records.
       Format of data table is: {time -> {src_ip -> {number_of_flows/packets/bytes}}}

       time: depends on interval that user set. If user set for example --interval 600,
       this parameter will have values like this 10:00:00, 10:10:00, 10:20:00. This timestamps means
       start of intervals in which records are aggregated.

       src_ip: ip addresses for which are data stored in current interval
       """

    data_table = dict()
    # current time = the maximum of all flow-end timestamps seen
    current_time = None
    # biflow = support for biflow data
    biflow = None
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
            for time in list(sorted(data_table.keys())):
                if current_time - time > timedelta(seconds=maxage):
                    queue.put((time, data_table[time]), block=True)
                    data_table.pop(time)

        while slot < current_time:
            slot = next(generator)
            data_table[slot] = {}

        if biflow is None:
            try:
                packets = trap.return_packets_rev()
                biflow = True
            except AttributeError as e:
                biflow = False

        data_aggregation(data_table, interval, trap, networks, biflow)

    # receive finished, put everything in the queue to send
    for time in list(sorted(data_table.keys())):
        queue.put((time, data_table[time]), block=True)

    # signal for thread to end
    queue.put("END", block=True)
    t1.join()

    if verbose:
        print("Finished.")


def replace_traphelp_in_argv(args):
    if args.traphelp:
        argv.remove('--traphelp')
        argv.extend(['-h', 'trap'])


def parse_arguments():
    parser = ArgumentParser(
        description='ADiCT input module. Collect input flows, aggregate and send them '
                    'as IP Activity intervals to the trap interface. '
                    'JSON formatted datapoints are sent to output Trap IFC.')

    parser.add_argument('--traphelp', help='display help for Trap IFC', action='store_true')

    parser.add_argument(
        '-i',
        help=('specification of interface types and their parameters, see '
              '"--traphelp" (mandatory parameter)'),
        type=str,
        metavar="IFC_SPEC"
    )

    parser.add_argument(
        '--interval', '-I',
        help=('Length of one time interval, in which flow records will be aggregated, in seconds. '
              '(default: 10 min).'),
        type=int,
        default=600,
        metavar="SECONDS"
    )

    parser.add_argument(
        '-m', '--maxage', help=('Max possible age of incoming data (in seconds). Data of time intervals older this '
                                'are sent and deleted (default: 20min).'),
        type=int,
        default=1200,
        metavar="SECONDS"
    )

    parser.add_argument('-s', help='Source tag', type=str, default="", metavar="SRC_TAG")

    parser.add_argument(
        "-N",
        "--networks",
        help=('IP networks (in CIDR format) to monitor. Only data of IPs from these networks will be included. '
              'Multiple networks can be separated by commas or spaces (quote the whole list in that case). '
              'If not set, all IPs are included.'),
        type=str,
        metavar="IPs",
        default="",
    )

    parser.add_argument('-v', '--verbose', help='Verbose mode', action='store_true')

    arg = parser.parse_args()

    if arg.maxage < arg.interval:
        print("Max data age can't be less than interval length.")
        sys.exit(1)

    if arg.networks:
        arg.networks = arg.networks.replace(',', ' ').split()
        for net in arg.networks:
            try:
                ipaddress.ip_network(net)
            except ValueError:
                print("Badly inserted ip address of network ", net)
                sys.exit(1)

    return arg


def main(inputspec):
    global verbose
    args = parse_arguments()
    replace_traphelp_in_argv(args)
    trap = TrapIfc(inputspec)

    verbose = args.verbose  # set global verbose flag

    if verbose:
        print("Watching IPs from networks:", ", ".join(map(lambda n: str(ipaddress.ip_network(n)), args.networks)))

    # precalculating networks and masks for faster ip filtering
    networks = list()
    for net in args.networks:
        n = ipaddress.ip_network(net)
        network = int(n.network_address)
        mask = int(n.netmask)

        networks.append([network, mask])

    input_processing(trap, args.interval, args.s, args.maxage, networks)


if __name__ == "__main__":
    main(inputspec)
