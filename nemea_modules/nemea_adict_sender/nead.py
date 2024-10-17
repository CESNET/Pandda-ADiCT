#!/usr/bin/env python3

import pytrap
import sys
import json
import requests
from argparse import ArgumentParser


parser = ArgumentParser(description="Receive ADiCT data-points as JSON messages on TRAP interface and send them via "
                                    "HTTP API to ADiCT server (or print to stdout if no URL is specified)."
                                    "A JSON-encoded list of objects (data-points) is expected on input.")
parser.add_argument("-i", "--ifcspec", metavar="IFCSPEC",
                    help="See https://nemea.liberouter.org/trap-ifcspec/")
parser.add_argument("-u", "--url", metavar="url",
                    help="Base URL of ADiCT server, e.g. http://example.com/adict/ (print data-points to stdout if not specified)")
parser.add_argument("-s", "--src", dest="src", metavar="SRC",
                    help="Name of this data source (add or overwrite the 'src' field in datapoints sent)")
parser.add_argument("-I", "--indent", metavar="N", type=int,
                    help="When writing to stdout, pretty-print JSON with indentation set to N spaces.")
parser.add_argument("-v", "--verbose", action="store_true",
                    help="Set verbose mode - print messages.")

args = parser.parse_args()

# Append "/datapoints" to the end of given URL, if it is not already there
url = args.url
if url and not url.endswith("/datapoints"):
    if url[-1] == "/":
        url += "datapoints"
    else:
        url += "/datapoints"

trap = pytrap.TrapCtx()
trap.init(["-i", args.ifcspec], 1, 0,)		# ifc spec
trap.setRequiredFmt(0, pytrap.FMT_JSON, "")

stop = False
# Main loop (trap.stop is set to True when SIGINT or SIGTERM is received)
while not stop:
    # Read data from input interface
    try:
        data = trap.recv()
    except pytrap.FormatMismatch:
        print("Error: output and input interfaces data type or format mismatch", file=sys.stderr)
        break
    except pytrap.FormatChanged as e:
        if args.verbose:
            print("Incoming TRAP data format:", trap.getDataFmt(0))
        data = e.data
        del(e)
        pass
    except (pytrap.Terminated, KeyboardInterrupt):
        break

    # Check for "end-of-stream" record
    if len(data) <= 1:
        if args.verbose:
            print("End-of-stream record received, going to quit.")
        break

    try:
        # Decode data (and check it's a valid JSON)
        rec_list = json.loads(data.decode("utf-8"))
    except ValueError as e:
        print(f"ERROR: Can't decode received data: {e}", file=sys.stderr)
        continue

    # Check format - must be a list of objects
    if type(rec_list) != list or any(type(rec) != dict for rec in rec_list):
        print("ERROR: Invalid format of incoming data, must be a list of objects.", file=sys.stderr)
        continue

    # Add "src" tag
    if args.src:
        for rec in rec_list:
            rec["src"] = args.src

    # Send to ADiCT (or print to stdout)
    if not url:
        print(json.dumps(rec_list, indent=args.indent))
    else:
        to_send = json.dumps(rec_list)
        if args.verbose:
            print("Sending:", to_send)
        try:
            resp = requests.post(url=url, data=to_send)
        except Exception as e:
            print(f"ERROR in HTTP POST request: {e}", file=sys.stderr)
            continue
        if args.verbose:
            print(f"Response: ({resp.status_code}) {resp.text[:1000]}") # print max 1000 chars of response

trap.finalize()
