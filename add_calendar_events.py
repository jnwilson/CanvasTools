#! /usr/bin/env python3
"""
add_calendar_events.py
    adds events to a Canvas calendar

    events_file
        Contains lines with tab-separated Event-Name and date in ISO 8601 format
        e.g.
              0x000VitalInformation   2021-08-23

    API_token file
        Canvas API token is stored in a file (default name: API_token)

"""

import sys
import argparse

import requests


def main():
    global events
    parser = argparse.ArgumentParser(description='Add events to a Canvas calendar')
    parser.add_argument('--course_id',
                        help='canvas course_id number (e.g., 439562',
                        required=True)
    parser.add_argument('--token_file',
                        help='Canvas Access Token File',
                        required=True)
    parser.add_argument('--event_file',
                        help='File containing lines of tab-separated event_name and ISO 8601 date',
                        required=True)
    parser.add_argument('-debug',
                        help='Set verbose debugging mode',
                        action='store_true')
    parser.add_argument('-n',
                        help='Dry run: do everything but submit grades',
                        action='store_true')

    args = parser.parse_args()

    # implement dry run some day
    if args.n:
        print(f'Dry run not yet implemented',
              file=sys.stderr,
              flush=True)
        exit(1)

    # Get token
    try:
        with open(args.token_file) as f:
            access_token = f.readline()
            f.close()
    except Exception as err:
        print(f"Couldn't read access token file {args.token_file}\n   {str(err)}",
              file=sys.stderr,
              flush=True)
        exit(2)
    # noinspection PyUnboundLocalVariable
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer ' + access_token.rstrip()}

    print(f'headers is [{headers}]')
    # Get events
    try:
        with open(args.event_file) as f:
            events = list(map(lambda line: line.rstrip().split('\t'), f.readlines()))
    except Exception as err:
        print(f"Couldn't parse event file {args.event_file}\n   {str(err)}",
              file=sys.stderr,
              flush=True)
        exit(3)

    calendar_uri = 'https://ufl.instructure.com/api/v1/calendar_events/'
    for (event, date) in events:
        try:
            print(f'Post request for [{event}]: [{date}]')
            post_response = requests.post(url=calendar_uri,
                                          headers=headers,
                                          params={'calendar_event[context_code]': f'course_{args.course_id}',
                                                  'calendar_event[title]': f'{event}',
                                                  'calendar_event[start_at]': f'{date}',
                                                  'calendar_event[end_at]': f'{date}'})
            print(f'{post_response.text}')
        except Exception as err:
            # noinspection PyUnboundLocalVariable
            print(f"Couldn't create event {str(err)}\n   {post_response.text}",
                  file=sys.stderr,
                  flush=True)


if __name__ == '__main__':
    main()