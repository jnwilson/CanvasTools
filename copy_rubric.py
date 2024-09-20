#! /usr/bin/env python3
# noinspection SpellCheckingInspection
"""
copy_rubric.py

Assumptions:
  0. You use the Canvas LMS for a class or several classes you are teaching or assisting with.
  1. The current directory where you are running this is a grades directory.
  2. You have a config file (default value: ./config*)
  3. You have a grading rubric .xlsx file (preferably in some other directory).
  4. You have a Canvas API Token in a file

"""

import sys
import argparse
import json
import os
import fnmatch
import requests
#import tempfile
#import numpy
#import typing
import shutil

# I really don't do that requirements.txt thing
# You'll probably have to pip3 install these:import requests
import csv


Software_Version = 0.5
SIS_ID_Index = 2

Debug = False
Dry_run = False

def paginated_get(url, headers, params):
    global Debug

    data_set = []

    while True:
        response = requests.get(url=url, headers=headers, params=params)
        result = json.loads(response.text)
        if Debug:
            print(f'url: {url}')
            print(f'headers: {headers}')
            print(f'params: {params}')
            print(f'result: {result}')
        data_set.extend(result)
        # stop when no more responses exit
        if response.links['current']['url'] == response.links['last']['url']:
            break
        url = response.links['next']['url']

    return response, data_set

def main():
    global Debug
    global Dry_run

    access_token = None
    asst_entry = None
    config = None

    parser = argparse.ArgumentParser(description='Copy rubric files')
    parser.add_argument('--config',
                        help='file containing config info (default: ./config*)',
                        default=None)
    parser.add_argument('--rubric',
                        help="rubric xlsx file for assignment (default: ./rubric*.xlsx)",
                        default=None)
    parser.add_argument('--token',
                        help='Canvas Access Token File (default: ../API_token)',
                        default='../API_token')
    parser.add_argument('-debug',
                        help='Set verbose debugging mode',
                        action='store_true')
    parser.add_argument('-n',
                        help='Dry run: do everything but submit grades',
                        action='store_true')

    args = parser.parse_args()
    Debug = args.debug

    uri_base = f'https://ufl.instructure.com/api/v1/'
    Dry_run = args.n

    # parse config file
    if not args.config:
        config_file = fnmatch.filter(os.listdir('.'), 'config*')
        assert not (len(config_file) < 1), 'No config file!'
        assert not (len(config_file) > 1), f'Too many config files:{config_file}'
        config_file = config_file[0]
    else:
        config_file = args.config

    try:
        with open(config_file) as f:
            config = json.load(f)
            f.close()
    except Exception as err:
        print(f'Unable to open or parse config file: [{config_file}]: {err}',
              file=sys.stderr,
              flush=True)
        exit(1)

    # Get rubric filename
    if not args.rubric:
        rubric_file = fnmatch.filter(os.listdir('.'), 'rubric*.xlsx')
        assert not (len(rubric_file) < 1), 'No rubric file!'
        assert not (len(rubric_file) > 1), f'Too many rubric files:{rubric_file}'
        rubric_file = rubric_file[0]
    else:
        rubric_file = args.config

    ##
    # read Canvas token from file
    try:
        with open(args.token) as f:
            access_token = f.readline()
            f.close()
    except Exception as err:
        print(f"Couldn't read API token file {args.token}\n   {err}",
              file=sys.stderr,
              flush=True)
        exit(2)

    headers = {'Authorization': f'Bearer {access_token.rstrip()}'}
    csv_headers = {'Content-Type': 'text/csv',
                   'Authorization': f'Bearer {access_token.rstrip()}'}

    assignment_map = config['quiz_ids']
    ##
    # Download submissions list
    for course_id in assignment_map.keys():
        try:
            assignment_submissions_rq_params = {'include': ['user']}
            assignment_submissions_uri = f'{uri_base}courses/{course_id}/assignments/{assignment_map[course_id]}/submissions'
            (assignment_submissions_response, data_set) = paginated_get(url=assignment_submissions_uri,
                                                                        headers=headers,
                                                                        params=assignment_submissions_rq_params)
            for entry_dict in data_set:
                name = entry_dict['user']['sortable_name']
                name = name.replace(' ','')
                name = name.replace(',','-')
                test_student_name = 'Student-Test'
                if name[:len(test_student_name)] == test_student_name:
                    name = f'Zz-{name}'
                new_filename = f'{name}-{entry_dict["user"]["id"]}-{course_id}.xlsx'
                try:
                    shutil.copy2(rubric_file, new_filename)
                    #print(new_filename.rstrip())
                except Exception as err:
                    print(f'Unable to create xlsx file for [{new_filename}]: {str(err)}',
                    file=sys.stderr,
                    flush=True)
                    exit(1)

        except Exception as err:
            print(f'copy_rubric failed:\n   {err}',
                  file=sys.stderr,
                  flush=True)


if __name__ == '__main__':
    main()
