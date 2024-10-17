#!/usr/bin/env python3
# Script to gather number of IP addresses per attribute of IP entity
# in Munin format.
#
# Author: Dávid Benko <david.benko@vut.cz>

import argparse
import json

from pymongo import ReadPreference

from dp3.common.attrspec import AttrType
from dp3.common.config import read_config_dir, ModelSpec
from dp3.database.database import MongoConfig, EntityDatabase

# Arguments parser
parser = argparse.ArgumentParser(description="IP count per attribute")
parser.add_argument("format", choices=["munin", "json"], help="Output format (munin or json)")
parser.add_argument(
    "--labels",
    action="store_true",
    default=False,
    help="Output only Munin-formatted attribute labels?",
)
parser.add_argument(
    "--config",
    default="/etc/adict/config",
    help="DP3 config directory (default: /etc/adict/config)",
)
args = parser.parse_args()

# Load DP3 configuration
config = read_config_dir(args.config, recursive=True)
entities = ModelSpec(config.get("db_entities"))

# Connect to database
connection_conf = MongoConfig.model_validate(config.get("database", {}))
client = EntityDatabase.connect(connection_conf)
client.admin.command("ping")

db = client.get_database(
    connection_conf.db_name, read_preference=ReadPreference.SECONDARY_PREFERRED
)

counts = {}
if not args.labels:
    for (etype, attr), spec in entities.attributes.items():
        label = f"{etype}-{attr}"

        if spec.t in AttrType.TIMESERIES | AttrType.OBSERVATIONS:
            field = f"#min_t2s.{attr}"
        else:
            field = f"{attr}.ts_last_update"
        pipeline = [
            {"$match": {field: {"$exists": True}}},
            {"$count": "count"},
        ]

        count = db[f"{etype}#master"].aggregate(pipeline)

        try:
            counts[label] = count.next()["count"]
        except StopIteration:
            counts[label] = 0

if args.format == "json":
    # Output data
    print(json.dumps(counts))
else:
    if args.labels:
        # Just list labels
        for (etype, attr), spec in entities.attributes.items():
            label = f"{etype}-{attr}"
            print(f"{label}.label {label}")
    else:
        # Output data
        for k, count in counts.items():
            print(f"{label}.value {count}")
