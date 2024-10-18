#!/usr/bin/env python3
"""
Check RabbitMQ telemetry data.

Fetches data from RabbitMQ and prints it as JSON.
"""
import json
from collections import defaultdict

import requests

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
    config = {
        "url": "http://localhost:15672",
        "user": "guest",
        "password": "guest",
    }

    output_data = {}

    try:
        response = requests.get(
            f"{config['url']}/api/queues",
            auth=(config["user"], config["password"]),
        )
        if response.status_code != 200:
            raise Exception(
                f"Failed to fetch data from RabbitMQ API. {response.status_code}, {response.text}"
            )

        data = response.json()

        for queue in data:
            appname, queue_name = queue["name"].split("worker-", 1)
            if len(queue_name) <= 2:
                queue_name += "-main"

            for key, alias in exported_queue_keys.items():
                value = queue[key]
                value_alias = f"{queue_name}-{alias}"
                output_data[f"{value_alias}"] = value

            if "message_stats" in queue:
                message_details = queue["message_stats"]
            else:
                message_details = defaultdict(lambda: defaultdict(float))

            for key, alias in exported_message_stats_keys.items():
                output_data[f"{queue_name}-{alias}"] = message_details[key]["rate"]

    except Exception as e:
        output_data["error"] = str(e)

    print(json.dumps(output_data, indent=2))
