#! /usr/bin/env python3
"""
create_groups.py

Assumptions:


    API_token file
        Canvas API token is stored in a file (default name: API_token)

"""
import sys
import argparse
import json
import os
import fnmatch
import re
import tempfile
import numpy

# I really don't do that requirements.txt thing
# You'll probably have to pip3 install these:
import requests
import csv

Software_Version = 0.5
SIS_ID_Index = 2

def main():
    access_token = None
    asst_entry = None
    config = None

    parser = argparse.ArgumentParser(description='Create canvas group names')
    parser.add_argument('--cid',
                        help='canvas Course ID (usually 6 digits)',
                        required=True)
    parser.add_argument('--csv_file',
                        required=True,
                        help='Attendance type CSV file')
    parser.add_argument('--assignments',
                        required=True,
                        help='Comma separated list of assignment group names')
    parser.add_argument('--token',
                        help='Canvas Access Token File',
                        default='../API_token')
    parser.add_argument('-debug',
                        help='Set verbose debugging mode',
                        action='store_true')
    parser.add_argument('-n',
                        help='Dry run: do everything but submit grades',
                        action='store_true')

    args = parser.parse_args()
    uri_base = f'https://ufl.instructure.com/api/v1/'
    ##
    # read Canvas token from file
    ##
    # read Canvas token from file
    try:
        with open(args.token) as f:
            access_token = f.readline()
            f.close()
    except Exception as err:
        print(f"Couldn't read access token file {args.token}\n   {err}",
              file=sys.stderr,
              flush=True)
        exit(2)

    headers = {'Authorization': f'Bearer {access_token.rstrip()}'}
    csv_headers = {'Content-Type': 'text/csv',
                   'Authorization': f'Bearer {access_token.rstrip()}'}
    ##
    # Read In-class vs online assignments from canvas grades file
    #
    in_class_students = []
    online_students = []
    try:
        with open(args.csv_file,'r') as csvfile:
            csv_reader = csv.reader(csvfile)
            # read gradefile column_names
            column_names = next(csv_reader)
            column_list = list(filter(lambda x: not x.find('Attendance'), column_names))
            column_number = column_names.index(column_list[0])
            assert len(column_list) == 1, 'Too many column names contain the word "Attendance"'
            # skip extra lines
            next(csv_reader)
            next(csv_reader)

            for row in csv_reader:
                if row[column_number] and int(float(row[column_number])) == 1:
                    in_class_students.append(row[SIS_ID_Index])
                else:
                    online_students.append(row[SIS_ID_Index])

    except Exception as err:
        print(f"Couldn't read csv file {args.csv_file}\n   {err}",
              file=sys.stderr,
              flush=True)
        exit(2)

    ##
    # Identify assignment group list
    assignments = args.assignments.split(',')
    print(f'assignments = {assignments}')

    ##
    # Create categories for each assignment
    for assignment in assignments:
        print(f'Creating assignment {assignment}')
        try:
            group_categories_rq_params = {'name': assignment,
                                          'auto_leader': 'first',
                                          }
            group_categories_uri = f'{uri_base}courses/{args.cid}/group_categories'
            if args.debug:
                print(f"uri = {group_categories_uri}")
            group_categories_response = requests.post(url=group_categories_uri,
                                                      headers=headers,
                                                      params=group_categories_rq_params)
            group_category_object = json.loads(group_categories_response.text)
            if args.debug:
                print(f'group_categories_response: {group_categories_response.text}')
        except Exception as err:
            print(err)
            print(f'* Create group categories request failed: {group_categories_response.text}\n   {err}',
                   file=sys.stderr,
                   flush=True)

        ##
        # Create randomized ordering of in-class vs. online students
        in_class_permutation = numpy.random.permutation(in_class_students)
        online_permutation = numpy.random.permutation(online_students)

        (temp_fd, temp_path) = tempfile.mkstemp(dir='/tmp')
        raw_data = b''
        if args.debug:
            print(f"Created file [{temp_path}]")
        group_number = 1
        # do groups of 3
        raw_data += str.encode('user_id,group_name,status\r\n')
        os.write(temp_fd, str.encode('user_id,group_name,status\r\n'))
        for this_permutation in (in_class_permutation, online_permutation):
            while len(this_permutation) > 4 or len(this_permutation) == 3:
                group_members = this_permutation[:3]
                this_permutation = this_permutation[3:]
                for group_member in group_members:
                    raw_data += str.encode(f'{group_member},{assignment} {str(group_number)},accepted\r\n')
                    os.write(temp_fd, str.encode(f'{group_member},{assignment} {str(group_number)},accepted\r\n'))
                group_number += 1
            while len(this_permutation) >2:
                group_members = this_permutation[:2]
                this_permutation = this_permutation[2:]
                for group_member in group_members:
                    raw_data += str.encode(f'{group_member},{assignment} {str(group_number)},accepted\r\n')
                    os.write(temp_fd, str.encode(f'{group_member},{assignment} {str(group_number)},accepted\r\n'))
                group_number += 1

        try:
            os.close(temp_fd)
            import_uri = f'{uri_base}group_categories/{group_category_object["id"]}/import'
            files = {'attachment': open(temp_path,'rb')}
            if args.debug:
                print(f'import_uri {import_uri}')
            import_response = requests.post(url=import_uri,
                                            data=raw_data,
                                            headers=csv_headers)
            if args.debug:
                print(f'import_response: {import_response.text}')
        except Exception as err:
            print(err)
            print(f'* Create group categories request failed: {import_response.text}\n   {err}',
                  file=sys.stderr,
                  flush=True)


if __name__ == '__main__':
    main()