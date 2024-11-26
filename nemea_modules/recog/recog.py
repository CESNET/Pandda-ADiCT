#!/usr/bin/env python3

import json
import re
import sys
import xml.etree.ElementTree as ET
from argparse import ArgumentParser
from datetime import datetime
from typing import Callable, Union

import pytrap

SSH_BANNER_REGEX = re.compile(r"^SSH-\d+\.\d+-")  # e.g. "SSH-2.0-"
SUPPORTED_POS_CATEGORIES = ["openssh", "service", "host", "os"]

parser = ArgumentParser(
    description="Receive SSH or SMTP banners and according to given database "
    "of known banners determine type of device or operating system "
    "and send it in ADiCT data point format in JSON to ADiCT server"
)

parser.add_argument(
    "-i",
    "--ifcspec",
    metavar="IFCSPEC",
    required=True,
    help="See https://nemea.liberouter.org/trap-ifcspec/",
)
parser.add_argument(
    "-d",
    metavar="DB_PATH",
    dest="db_path",
    required=True,
    help="Path to database (xml file) with ssh/smtp banners",
)
parser.add_argument(
    "-m",
    metavar="MODE",
    choices=["smtp", "ssh", "server", "setcookie"],
    dest="mode",
    required=True,
    help="Mode of detector 4 options: 'smtp', 'ssh', 'server' or 'setcookie'",
)
parser.add_argument(
    "-v",
    "--verbose",
    action="store_true",
    help="Print all banners and their matching information to stdout.",
)
args = parser.parse_args()
path = args.db_path
mode = args.mode
verbose = args.verbose
trap = pytrap.TrapCtx()
try:
    trap.init(["-i", args.ifcspec], 1, 1)
except pytrap.TrapError as e:
    print(f"PyTrap: {e}", file=sys.stderr)
    sys.exit(1)

# Load the XML file
try:
    tree = ET.parse(path)
except Exception as e:
    print(f"Can't open xml file: {e}", file=sys.stderr)
    trap.finalize()
    sys.exit(1)

root = tree.getroot()
pattern_regex = []
# Create a dictionary to store the fingerprints
fingerprints = {}
# Iterate over each fingerprint element
for fingerprint in root.iter("fingerprint"):
    # Extract the pattern attribute value as the dictionary key
    pattern = fingerprint.get("pattern")

    # Create a dictionary to store the fingerprint parameters
    os = {}
    service = {}
    hw = {}
    openssh = {}
    host = {}
    position = {}

    # Iterate over each param element
    for param in fingerprint.iter("param"):
        # Extract the name and value attributes
        pos = param.get("pos")
        name = param.get("name")
        value = param.get("value")

        pos = int(pos)
        if name != "cookie":
            category, item = name.split(".", 1)
        if (value is None) and (pos == 0):
            continue
        if category == "os":
            os[item] = value
        elif category == "service":
            service[item] = value
        elif category == "hw":
            hw[item] = value
        elif category == "openssh":
            openssh[item] = value
        elif category == "host":
            host[item] = value
        if pos != 0 and category in SUPPORTED_POS_CATEGORIES:
            position[name] = pos

    # if record has no information continue to next one
    if not (os or service or hw):
        continue

    params = {}
    if os:
        params["os"] = os
    if service:
        params["service"] = service
    if hw:
        params["hw"] = hw
    if openssh:
        params["openssh"] = openssh
    if host:
        params["host"] = host
    if position:
        params["position"] = position
    # Add the fingerprint to the dictionary
    fingerprints[pattern] = params
    pattern_regex.append(pattern)

compiled_patterns = [re.compile(pattern) for pattern in pattern_regex]


def sanitize_banner(banner: str) -> str:
    """Replace non-printable characters by '·' (for verbose prints)"""
    return "".join(c if c.isprintable() else "·" for c in banner)


def create_datapoint(rec: pytrap.UnirecTemplate, data: dict, mode: str, ip: str) -> str:
    tmpdic = {
        "type": "ip",
        "id": ip,
        "attr": mode,
        "v": data,
        "t1": datetime.isoformat((rec.TIME_FIRST).toDatetime()),
        "t2": datetime.isoformat((rec.TIME_LAST).toDatetime()),
        "src": "",
    }
    datapoint = json.dumps([tmpdic])
    return datapoint


def ssh_extract_banners(
    rec: pytrap.UnirecTemplate,
) -> Union[tuple[list[str], str], None]:
    content = rec.IDP_CONTENT_REV
    try:
        content = content.decode("utf-8").strip()
    except UnicodeDecodeError:
        return None

    if verbose:
        print(sanitize_banner(content))

    if not SSH_BANNER_REGEX.match(content):
        if verbose:
            print("-> UNEXPECTED BANNER FORMAT")
        return None  # not an expected content ("SSH-x.y-")

    # remove header of SSH version ("SSH-x.y-")
    content = content.split("-", 2)[2]
    return [content], str(rec.DST_IP)


def smtp_extract_banners(
    rec: pytrap.UnirecTemplate,
) -> Union[tuple[list[str], str], None]:
    content = rec.IDP_CONTENT_REV
    try:
        content = content.decode("utf-8").strip()
    except UnicodeDecodeError:
        return None

    if verbose:
        print("banner:", sanitize_banner(content))

    if not content.startswith("220 "):
        if verbose:
            print("-> UNEXPECTED BANNER FORMAT")
        return None  # not an expected content

    # remove the code ("220 ") from the beginning of the content
    content = content[4:]
    return [content], str(rec.DST_IP)


def http_server_extract_banners(
    rec: pytrap.UnirecTemplate,
) -> Union[tuple[list[str], str], None]:
    try:
        server = rec.HTTP_RESPONSE_SERVER
    except UnicodeDecodeError:
        return None
    return [server], str(rec.SRC_IP)


def http_setcookie_extract_banners(
    rec: pytrap.UnirecTemplate,
) -> Union[tuple[list[str], str], None]:
    cookie_names = rec.HTTP_RESPONSE_SET_COOKIE_NAMES.split(";")
    if cookie_names[0]:
        cookie = [name + "=" for name in cookie_names]
        cookie_names = cookie_names + cookie
        return cookie, str(rec.SRC_IP)
    return None


def get_data(record: str):
    for patt in compiled_patterns:
        match = patt.search(record)
        if match:
            if verbose:
                print(f"-> MATCH: {fingerprints[patt.pattern]}")
            data = fingerprints[patt.pattern]

            position = data.pop("position", False)
            if position:
                # iterate through position dictionary
                # and add to data dict information from regex match
                for name, pos in position.items():
                    if name == "cookie":
                        continue
                    else:
                        category, item = name.split(".", 1)
                    value = match.group(pos)
                    if value is None:
                        data[category].pop(item)
                        if not data[category]:
                            data.pop(category)
                        continue
                    # store the obtained information to data dictionary
                    data[category][item] = value

                    # replace part of cpe23 value with the obtained information
                    if name == "service.version":
                        if "cpe23" in data["service"]:
                            data["service"]["cpe23"] = data["service"]["cpe23"].replace(
                                "{service.version}", value
                            )
                    elif name == "os.version" and "cpe23" in data["os"]:
                        data["os"]["cpe23"] = data["os"]["cpe23"].replace(
                            "{os.version}", value
                        )

            return data

    if verbose:
        print("-> UNKNOWN BANNER")
    return ""


def do_detection(
    rec: pytrap.UnirecTemplate,
    extract_data: Callable[[pytrap.UnirecTemplate], Union[tuple[list[str], str], None]],
    mode: str,
):
    result_or_none = extract_data(rec)
    if result_or_none is None:
        return
    records, ip = result_or_none
    for record in records:
        data = get_data(record)
        if data:
            datapoint = create_datapoint(rec, data, mode, ip)
            trap.send(bytearray(datapoint, "utf-8"))


# Set the list of required fields in received messages.
if mode == "ssh":
    extract_data = ssh_extract_banners
    inputspec = "ipaddr DST_IP,bytes IDP_CONTENT_REV,time TIME_FIRST,time TIME_LAST"
elif mode == "smtp":
    extract_data = smtp_extract_banners
    inputspec = "ipaddr DST_IP,bytes IDP_CONTENT_REV,time TIME_FIRST,time TIME_LAST"
elif mode == "server":
    extract_data = http_server_extract_banners
    inputspec = (
        "ipaddr SRC_IP,string HTTP_RESPONSE_SERVER,time TIME_FIRST,time TIME_LAST"
    )
else:
    extract_data = http_setcookie_extract_banners
    inputspec = (
        "ipaddr SRC_IP,string HTTP_RESPONSE_SET_COOKIE_NAMES,"
        "time TIME_FIRST,time TIME_LAST"
    )

trap.setRequiredFmt(0, pytrap.FMT_UNIREC, inputspec)
rec = pytrap.UnirecTemplate(inputspec)
trap.setDataFmt(0, pytrap.FMT_JSON, "adict_datapoint")

mode = "recog_" + mode


# Main loop
while True:
    try:
        data = trap.recv()
    except pytrap.FormatChanged as e:
        fmttype, inputspec = trap.getDataFmt(0)
        rec = pytrap.UnirecTemplate(inputspec)
        data = e.data
    if len(data) <= 1:
        break
    rec.setData(data)
    do_detection(rec, extract_data, mode)

# Free allocated TRAP IFCs
trap.finalize()
