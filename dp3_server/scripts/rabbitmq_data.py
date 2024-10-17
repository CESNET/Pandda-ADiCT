#!/usr/bin/env python3
"""
Script to check RabbitMQ telemetry data.
"""
import argparse
import json

import icinga
import requests


def get_age_seconds(timestamp, now):
    return (now - timestamp).total_seconds()


exported_queue_keys = {
    "messages": "total",
    "messages_ready": "ready",
    "messages_unacknowledged": "unacked",
    "consumers": "consumers",
    "memory": "memory",
    "message_bytes": "message_bytes",
}

exported_message_stats_keys = {
    "publish_details": "incoming",
    "deliver_get_details": "outgoing",
}

if __name__ == "__main__":
    config = icinga.ConfigParser(
        section={"dp3": ["python", "source_age_script", "cfg_path"]},
    )

# Arguments parser
parser = argparse.ArgumentParser(
    description="Returns RabbitMQ telemetry data (designed for Icinga)"
)
parser.add_argument("--url", default="http://localhost:15672")
parser.add_argument("--user", default="guest")
parser.add_argument("--password", default="guest")
args = parser.parse_args()

# Get data
response = requests.get(f"{args.url}/api/queues", auth=(args.user, args.password))
if response.status_code != 200:
    print(response.text)
    raise Exception("Failed to get RabbitMQ data")

data = response.json()
output_data = {}

for queue in data:
    appname, queue_name = queue["name"].split("worker-", 1)
    if len(queue_name) <= 2:
        queue_name += "-main"
    for key, alias in exported_queue_keys.items():
        output_data[f"{queue_name}-{alias}"] = queue[key]

    message_details = queue["message_stats"]
    for key, alias in exported_message_stats_keys.items():
        output_data[f"{queue_name}-{alias}"] = message_details[key]["rate"]

# Print results
print(json.dumps(output_data, indent=4, default=str))
