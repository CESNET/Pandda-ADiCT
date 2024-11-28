#!/usr/bin/env python3

import json
import signal
import sys
import threading
import time
from argparse import ArgumentParser
from collections import defaultdict
from datetime import datetime

import pytrap

parser = ArgumentParser(
    description="Receive ADiCT data-points as JSON messages on TRAP interface,"
    " aggregate them and send them via TRAP interface. "
    "A JSON-encoded list of objects (data-points) is expected on input."
)
parser.add_argument(
    "-i",
    "--ifcspec",
    metavar="IFCSPEC",
    help="See https://nemea.liberouter.org/trap-ifcspec/",
)
parser.add_argument(
    "-S",
    "--send-interval",
    type=int,
    metavar="seconds",
    default=900,
    help="Set the period of sending data to output (in seconds, default: 900)",
)
parser.add_argument(
    "-v", "--verbose", action="store_true", help="Set verbose mode - print messages."
)

args = parser.parse_args()

# Storage for aggregated data-points
aggregated_data = defaultdict(
    lambda: {
        "t1": datetime.max.isoformat(),
        "t2": datetime.min.isoformat(),
        "c": 0.0,
        "src": set(),
    }
)
# Lock to prevent concurrent access to aggregated_data
lock = threading.Lock()
# Stop flags
stop_flag_recv = (
    threading.Event()
)  # used to exit the data receiving loop after a signal is received
stop_flag_send = (
    threading.Event()
)  # used to stop the sending thread after the receiving loop stops


def process_data_points(dp):
    for data in dp:
        key = (
            data["type"],
            data["id"],
            data["attr"],
            json.dumps(data["v"], sort_keys=True),
        )
        with lock:
            rec = aggregated_data[key]
            rec["t1"] = min(rec["t1"], data["t1"])
            rec["t2"] = max(rec["t2"], data["t2"])

            if "c" in data:
                rec["c"] = max(rec["c"], data["c"])
            else:
                rec["c"] = 1.0

            if data["src"]:
                rec["src"].add(data["src"])


def sending_thread_func(trap, send_interval):
    while True:
        # Compute the next boundary of a time interval
        now = time.time()
        interval_end = now - (now % send_interval) + send_interval
        # Wait until the end of the time interval or the stop flag is set
        if args.verbose:
            print(
                f"{datetime.now().isoformat()}: Waiting for next interval boundary at "
                f"{datetime.fromtimestamp(interval_end).isoformat()} ...",
                flush=True,
            )
        do_stop = stop_flag_send.wait(max(0, interval_end - time.time()))
        # Send content aggregated_data to output interface
        with lock:
            aggregated_data_copy = aggregated_data.copy()
            aggregated_data.clear()
        send_aggregated_data(trap, aggregated_data_copy)
        if do_stop:
            break  # stop_flag was set -> stop thread


def send_aggregated_data(trap, aggregated_data_copy):
    if args.verbose:
        print(
            f"{datetime.now().isoformat()}: "
            f"Sending {len(aggregated_data_copy)} aggregated datapoints ...",
            flush=True,
        )

    for key, data in aggregated_data_copy.items():
        aggregated_dp = {
            "type": key[0],
            "id": key[1],
            "attr": key[2],
            "v": json.loads(key[3]),
            "t1": data["t1"],
            "t2": data["t2"],
            "c": data["c"],
            "src": ",".join(data["src"]),
        }
        datapoint = json.dumps([aggregated_dp])
        trap.send(bytearray(datapoint, "utf-8"))
    if args.verbose:
        print(f"{datetime.now().isoformat()}: Done", flush=True)


def process_input_data(trap):
    # Main loop (trap.stop is set to True when SIGINT or SIGTERM is received)
    while not stop_flag_recv.is_set():
        # Read data from input interface
        try:
            data = trap.recv()
        except pytrap.FormatMismatch:
            print(
                "Error: output and input interfaces data type or format mismatch",
                file=sys.stderr,
            )
            break
        except pytrap.FormatChanged as e:
            if args.verbose:
                print("Incoming TRAP data format:", trap.getDataFmt(0), flush=True)
            data = e.data
            del e
            pass
        except pytrap.Terminated:
            break

        # Check for "end-of-stream" record
        if len(data) <= 1:
            if args.verbose:
                print("End-of-stream record received, going to quit.", flush=True)
            break

        try:
            # Decode data (and check it's a valid JSON)
            rec_list = json.loads(data.decode("utf-8"))
        except ValueError as e:
            print(f"ERROR: Can't decode received data: {e}", file=sys.stderr)
            continue

        process_data_points(rec_list)

    # Input processing finished, stop the sending thread
    stop_flag_send.set()


def stop_program(signum, frame):
    # Stop receiving input data
    stop_flag_recv.set()
    # Reset signal handlers to default, so second signal closes the program immediately
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    signal.signal(signal.SIGTERM, signal.SIG_DFL)
    signal.signal(signal.SIGABRT, signal.SIG_DFL)
    if args.verbose:
        print(
            "Signal received. Going to stop the program after the cached data are sent."
            " Press Ctrl-C again to exit immediately.",
            flush=True,
        )


trap = pytrap.TrapCtx()
trap.init(["-i", args.ifcspec], 1, 1)
trap.setRequiredFmt(0, pytrap.FMT_JSON, "")
trap.setDataFmt(0, pytrap.FMT_JSON, "adict_datapoint")

# Register signal handler on common stopping signals - sets the "stop_flag_recv" event
signal.signal(signal.SIGINT, stop_program)
signal.signal(signal.SIGTERM, stop_program)
signal.signal(signal.SIGABRT, stop_program)

# Create and start the sending thread
sending_thread = threading.Thread(
    target=sending_thread_func, args=(trap, args.send_interval)
)
sending_thread.start()

# Start processing input data (in the main thread)
process_input_data(trap)

sending_thread.join()
trap.finalize()
