import boto3
from datetime import datetime,  timezone
import argparse
import json
import os

def parse_time(timestr):
    # Parse input format "08/08/25 06:46:00" as MM/DD/YY HH:MM:SS
    dt = datetime.strptime(timestr, "%d/%m/%y %H:%M:%S").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000) 

def fetch_logs(log_group, start_time_ms, end_time_ms, output_file, profile, strip):
    boto3.Session(profile_name = profile, region_name="eu-central-1")
    os.environ["AWS_PROFILE"] = profile
    client = boto3.client('logs')
    print("Profile: "+ profile)

    next_token = None
    all_events = []

    print(f"Fetching logs from {log_group} between {start_time_ms} and {end_time_ms}...")

    while True:
        kwargs = {
            'logGroupName': log_group,
            'startTime': start_time_ms,
            'endTime': end_time_ms,
            'limit': 10000,
        }
        if next_token:
            kwargs['nextToken'] = next_token
        
        response = client.filter_log_events(**kwargs)
        events = response.get('events', [])
        all_events.extend(events)
        
        next_token = response.get('nextToken')
        if not next_token:
            break

    print(f"Fetched {len(all_events)} log events. Saving to {output_file}...")

    with open(output_file, "w", encoding="utf-8") as f:
        for event in all_events:
            if strip:
                message =event.get("logStreamName","")[-3:]+":" + event.get("message", "")
                f.write(message + "\n")
            else:
                f.write(json.dumps(event) + "\n")

def main():
    parser = argparse.ArgumentParser(description="Download CloudWatch logs for given time and log group")
    parser.add_argument("start_time", help='Start time in format "DD/MM/YY HH:MM:SS" (e.g. "08/08/25 06:46:00")')
    parser.add_argument("log_group", help="CloudWatch Logs log group name")
    parser.add_argument("--duration", type=int, default=5, help="Duration in minutes to fetch logs from start time (default 5)")
    parser.add_argument("--strip", type=bool, default=False, help="strips non message part of the logs, (makes them more readable)")
    parser.add_argument("--profile", default="wh-dev-admin", help="AWS CLI profile name to use")
    args = parser.parse_args()

    start_ms = parse_time(args.start_time)
    end_ms = start_ms + args.duration * 60 * 1000
    args.output = str(args.log_group) + str(args.start_time).replace(" ","_").replace("/","_").replace(":","_") + "d"+str(args.duration) + "logs.txt"

    fetch_logs(args.log_group, start_ms, end_ms, args.output, args.profile, args.strip)

if __name__ == "__main__":
    main()
