#! /usr/bin/env python3
"""
submit_grades.py

Assumptions:

   Excel files:
       There is an excel file for each student that contains two specific columns
       Category and Deductions
       The student's score is in the Row having Category 'Score' in the Deductions column

       The excel filename has form   XXXXX,#####.xlsx
       where XXXXX is some representation of the student name and
       ##### is the students canvas_student_id

    config file
        json dictionary with entries course_id and assignment_id

    API_token file
        Canvas API token is stored in a file (default name: API_token)

"""
import sys
import argparse
import json
import os
import fnmatch

# I really don't do that requirements.txt thing
# You'll probably have to pip3 install these:
import requests
import pandas

Software_Version = 0.4


def main():
    access_token = None
    assignment_id = None
    asst_entry = None
    config = None
    response = None

    parser = argparse.ArgumentParser(description='Copy Rubric to student files')
    parser.add_argument('--config',
                        help='file containing config info',
                        default=None)

    parser.add_argument('--token',
                        help='Canvas Access Token File',
                        default='../API_token')

    parser.add_argument('-debug',
                        help='Set verbose debugging mode',
                        action='store_true')
    parser.add_argument('-force',
                        help='Perform action without user acknowledgement',
                        action='store_true')
    parser.add_argument('-n',
                        help='Dry run: do everything but submit grades',
                        action='store_true')

    args = parser.parse_args()

    ##
    # read config file
    #
    # json config file example
    #
    # {"software_version": 0.2,
    #  "assignment_name": "P0x01",
    #  "score_column": "Total",
    #  "course_id": 3482356,
    #  "assignment_id": 03823646}

    ##
    # grab config filename if not set

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
    except Exception as err:
        print(f'Unable to open or parse config file: [{config_file}]: {str(err)}',
              file=sys.stderr,
              flush=True)
        exit(1)

    ##
    # check software version

    config_software_version = config['software_version']
    assert Software_Version >= config_software_version, \
        f'Software version ({str(Software_Version)}) too low. ' \
        f'Config file requires {str(config_software_version)}'

    score_column = config['score_column'] if 'score_column' in config.keys() else 'Deductions'
    score_label = config['score_label'] if 'score_label' in config.keys() else 'Score'

    ##
    # read Canvas token from file
    try:
        with open(args.token) as f:
            access_token = f.readline()
            f.close()
    except Exception as err:
        print(f"Couldn't read access token file {args.token}\n   {str(err)}",
              file=sys.stderr,
              flush=True)
        exit(2)

    assignment_uri = 'https://ufl.instructure.com/api/v1/courses/' + \
        str(config['course_id']) + '/assignments/' + \
        str(config['assignment_id'])

    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer ' + access_token.rstrip()}

    ##
    # find assignment id
    assignments_uri = 'https://ufl.instructure.com/api/v1/courses/' + \
                      str(config['course_id']) + '/assignments/'
    assignments_response = requests.get(url=assignments_uri,
                                        headers=headers,
                                        params={'per_page': '500'})

    assignments = json.loads(assignments_response.text)

    if args.debug:
        print(f'assignments_uri:{assignments_uri}:{headers}')
    try:
        if args.debug:
            print(f'config["assignment_id"] is {config["assignment_id"]}',
                  flush=True)
        asst_entry = list(filter(lambda x: 'id' in x and x['id'] == config['assignment_id'], assignments))
        assignment_id = asst_entry[0]["id"]
    except Exception as err:
        print(f'* Could not find assignment for assignment {config["assignment_id"]}\n   {str(err)}',
              file=sys.stderr,
              flush=True)
        exit(254)

    ##
    # Get verification of correct exercise

    exercise_name = asst_entry[0]['name']
    config_name = config['assignment_name']
    if not args.force:
        if input(f'\nExercise name is: {exercise_name}\nConfigured name:  '
                 f'{config_name}\n\nDo you want to continue? [y/n] ') != 'y':
            exit(1)

    ##
    # get assignment submissions
    submissions_uri = assignment_uri + '/submissions'

    params = {'per_page': '500'}
    submissions_response = requests.get(url=submissions_uri,
                                        headers=headers,
                                        params=params)
    if args.debug:
        print(f'{submissions_uri}&{params}:{headers}')
    #    print(f'submissions_response.text:{submissions_response.text}')
    submissions = json.loads(submissions_response.text)

    ##
    # convert each students xlsx grade file to csv
    # and upload student grade

    excel_files = fnmatch.filter(os.listdir('.'), '*[0-9]*.xlsx')

    for this_xlsx_filename in excel_files:
        print(f'--Working on {this_xlsx_filename}',
              flush=True)

        ##
        # create corresponding csv file
        try:
            this_xlsx = pandas.read_excel(this_xlsx_filename)

        except Exception as err:
            print(f'* Cannot read excel file [{this_xlsx_filename}]\n   {str(err)}',
                  file=sys.stderr)
            continue

        ##
        # extract score from csv file
        try:
            score = -1
            for row_ind in range(len(this_xlsx)-1, -1, -1):
                if this_xlsx.at[row_ind, list(this_xlsx)[0]] == score_label:
                    score = this_xlsx.at[row_ind, score_column]
                    print(f'Score is {score}')
                    if 'factor' in config.keys():
                        score = score*config['factor']
            assert(score != -1)
        except Exception as err:
            print(f'* Score not found for [{this_xlsx_filename}]\n   {str(err)}',
                  file=sys.stderr,
                  flush=True)
            continue

        # grab Canvas student ID from filename
        student_canvas_id = this_xlsx_filename.split(',')[1].split('.')[0]
        if args.debug:
            print(f'**student_canvas_id: {student_canvas_id}',
                  flush=True)

        ##
        # upload excel comments
        comment_upload_uri = f'{assignments_uri}{str(assignment_id)}/submissions/{str(student_canvas_id)}'

        if args.debug:
            print(f'**comment_upload_uri: {comment_upload_uri}',
                  flush=True)

        if not args.n:
            try:
                upload_rq_params = {'name': this_xlsx_filename,
                                    'size': str(os.stat(this_xlsx_filename).st_size),
                                    'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                    'on_duplicate': 'overwrite'}
                upload_rq_uri =\
                    f'{assignments_uri}{str(assignment_id)}/submissions/{str(student_canvas_id)}/comments/files/'
                upload_rq_response = requests.post(url=upload_rq_uri,
                                                   headers=headers,
                                                   params=upload_rq_params)
                upload_rq = json.loads(upload_rq_response.text)
                upload_uri = upload_rq['upload_url']

                do_upload_response = requests.post(url=upload_uri,
                                                   params=upload_rq['upload_params'],
                                                   files={'file': open(this_xlsx_filename, 'rb')})
                print(f'upload_uri is {upload_uri}')
                print(f'upload_response is {do_upload_response} : {do_upload_response.text}')
                do_upload = json.loads(do_upload_response.text)

                if do_upload_response.status_code == 201:
                    confirmation_response = requests.post(url=do_upload['location'],
                                                          headers=headers,
                                                          params={'Content-Length': '0'})
                else:
                    assert int(do_upload_response.status_code/100) == 3, 'Erroneous status code from upload'
                    confirmation_response = requests.get(url=do_upload['location'])

                print(f'confirmation response is {confirmation_response.text}')

                confirmation = json.loads(confirmation_response.text)
                comment_addfile = requests.put(url=comment_upload_uri,
                                               headers=headers,
                                               params={'comment[file_ids][]': f'{str(confirmation["id"])}'})
                print(f'comment_addfile " {comment_addfile.text}')

            except Exception as err:
                print(f'* Excel comment file upload failed]\n   {str(err)}',
                      file=sys.stderr,
                      flush=True)

        ##
        # find student id in submissions
        try:
            assignment_entry = list(filter(lambda x: 'user_id' in x and x['user_id'] == int(student_canvas_id),
                                           submissions))
            last_entry = assignment_entry[-1]
        except Exception as err:
            print(f'* Could not find assignment entry for {this_xlsx_filename}\n   {str(err)}',
                  file=sys.stderr,
                  flush=True)
            continue

        submission_id = last_entry["id"]
        attempt = last_entry["attempt"]
        if args.debug:
            print(f'**submission_id: {str(submission_id)}, attempt is {str(attempt)}',
                  flush=True)

        for this_attempt in range(1, attempt+1):
            # Set all earlier attempts to 0 (to insure only one grade prevails
            # just in case use highest grade is set.
            # This is something people might want to change.
            this_score = 0 if this_attempt < attempt else score
            this_score = float(this_score)

            request_uri = submissions_uri + '/' + student_canvas_id

            if args.debug:
                print(f'**request_uri {request_uri}',
                      flush=True)
                print(f'headers={headers}',
                      flush=True)
            if not args.n:
                params = {'submission[posted_grade]': str(this_score)}
                try:
                    response = requests.put(url=request_uri,
                                            headers=headers,
                                            params=params)
                    if this_attempt == attempt:
                        print(f'request: {request_uri}:{params}')
                        print(f'Uploaded grade {str(this_score)} for {this_xlsx_filename}',
                              flush=True)
                except Exception as err:
                    print(f'**http request failed {request_uri}\nresponse: {response.text}\n   {str(err)}',
                          file=sys.stderr,
                          flush=True)
            else:
                if this_attempt == attempt:
                    print(f'No action for {this_xlsx_filename}',
                          flush=True)

    if args.n:
        print('No upload actions actually performed',
              flush=True)


if __name__ == '__main__':
    main()
