#!/usr/bin/env python3
# Munin script to check age of ADiCT data by source.
#
# Authors: Dávid Benko <david.benko@vut.cz>, Ondřej Sedláček <xsedla1o@stud.fit.vutbr.cz>

import argparse
import json
from datetime import datetime, timezone

from dp3.common.config import read_config_dir
from dp3.database.database import MongoConfig, EntityDatabase


def get_age_in_minutes(timestamp, now):
    return int((now - timestamp.replace(tzinfo=timezone.utc)).total_seconds() / 60)


# Arguments parser
parser = argparse.ArgumentParser(
    description="Return age of the latest data-point of each attribute in ADiCT "
    "(designed for Munin plugin and Icinga plugin)"
)
parser.add_argument("format", choices=["munin", "json"], help="Output format (munin or json)")
parser.add_argument(
    "--labels",
    action="store_true",
    default=False,
    help="Output only Munin-formatted attribute labels?",
)
parser.add_argument(
    "--warning",
    metavar="MIN:MAX",
    help="Add 'warning' parameter with given value to each label for Munin (only with --labels)",
)
parser.add_argument(
    "--config",
    default="/etc/adict/config",
    help="DP3 config directory (default: /etc/adict/config)",
)
args = parser.parse_args()

# Load DP3 configuration
config = read_config_dir(args.config, recursive=True)

# Connect to database
connection_conf = MongoConfig.model_validate(config.get("database", {}))
client = EntityDatabase.connect(connection_conf)
client.admin.command("ping")

db = client[connection_conf.db_name]

# Get latest data-point age for each attribute
now = datetime.now().astimezone(timezone.utc)
cached_results = list(db["#cache#Telemetry"].find())

# Get results
source_ages = {
    doc["_id"]: get_age_in_minutes(doc["src_t"], now)
    for doc in sorted(cached_results, key=lambda x: x["_id"])
}

# Print results
if args.format == "json":
    print(json.dumps(source_ages))
else:
    for source, age_minutes in source_ages.items():
        if args.labels:
            print(f"{source}.label {source}")
            if args.warning:
                print(f"{source}.warning {args.warning}")

        else:
            print(f"{source}.value {age_minutes}")
