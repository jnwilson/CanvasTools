#! /usr/bin/env python3
"""
submit_assignment.py

Assumptions:

Excel files:
There is an excel file for each student with a score_label and a score_column

    The names of the column and the first entry in the score row
    are either default (Deductions and Score, resp.) or given by
    the appropriate entries in the config file

    The student's score for the assignment score_row, score_column entry

The excel filenames have form   NNNN-SSSS-CCCC.xlsx
where NNNN is some representation of the student name and course number,
SSSS is the student's canvas_student_id, and
CCCC is the canvas_course_id in which the student is registered.

config file
        json dictionary with entries course_id and assignment_id
        and possibly having entries score_column and score_label

    API_token file
        Canvas API token is stored in a file (default name: API_token)

"""
import sys
import argparse
import json
import os
import fnmatch
import re

# I really don't do that requirements.txt thing
# You'll probably have to pip3 install these:
import requests
import pandas

Software_Version = 0.5


def main():
    access_token = None
    asst_entry = None
    config = None

    parser = argparse.ArgumentParser(description='Submit a graded Canvas assignment')
    parser.add_argument('--config',
                        help='file containing config info',
                        default=None)
    parser.add_argument('--token',
                        help='Canvas Access Token File',
                        default='../API_token')
    parser.add_argument('-comments_only',
                       help='Only submit comments -- no grades',
                       action='store_true')
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
        print(f"Couldn't read access token file {args.token}\n   {err}",
              file=sys.stderr,
              flush=True)
        exit(2)

    # Prepare information for associating assignments with courses
    assignment_map = config['quiz_ids']
    assignment_uri_base = 'https://ufl.instructure.com/api/v1/courses/'

    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer ' + access_token.rstrip()}
    assignment_id_map = {}
    saved_config_name = ''

    # Verify assignment ids for courses actually exist
    for course_id in assignment_map.keys():
        assignments_uri = f'{assignment_uri_base}{course_id}/assignments/'
        assignments_response = requests.get(url=assignments_uri,
                                            headers=headers,
                                            params={'per_page': '500'})
        assignments = json.loads(assignments_response.text)

        if args.debug:
            print(f'assignments_uri:{assignments_uri}:{headers}',
                  file=sys.stderr)
            # print(f'assignments:{assignments}')
        try:
            if args.debug:
                print(f'config["assignment_map[course_id]"] is {assignment_map[course_id]}',
                      flush=True)
            asst_entry = list(filter(lambda x: 'quiz_id' in x and str(x['quiz_id']) == assignment_map[course_id],
                                     assignments))
            if args.debug:
                print(f'asst_entry (quizzes):{asst_entry}')
            if not asst_entry:
                asst_entry = list(filter(lambda x: 'id' in x and str(x['id']) == assignment_map[course_id], assignments))
                if args.debug:
                    print(f'asst_entry (assignments):{asst_entry}')
            assignment_id_map[course_id] = asst_entry[0]["id"]
        except Exception as err:
            print(f'* Could not find assignment {assignment_map[course_id]} in course {course_id}\n   {err}',
                  file=sys.stderr,
                  flush=True)
            # print(f'assignments:{assignments}')
            exit(254)

        ##
        # Get verification of correct exercise
        # (one time only if they match across sections)
        exercise_name = asst_entry[0]['name']
        config_name = config['assignment_name']
        if not args.force and config_name != saved_config_name:
            if input(f'\nExercise name is: {exercise_name}\nConfigured name (Course {course_id}):  '
                     f'{config_name}\n\nContinue? [y/n] ') != 'y':
                exit(1)
        saved_config_name = config_name

        ##
        # Actually,  DON'T get assignment submissions
        # submissions_uri_map[course_id] = f'{assignments_uri}/{assignment_id_map[course_id]}/submissions'

        # params = {'per_page': '5000'}
        # submissions_response = requests.get(url=submissions_uri_map[course_id],
        #                                     headers=headers,
        #                                     params=params)
        # if args.debug:
        #     print(f'{submissions_uri_map[course_id]}&{params}:{headers}',
        #           file=sys.stderr)

        # submissions_map[course_id] = json.loads(submissions_response.text)

    ##
    # Upload each student's xlsx file.
    excel_files = fnmatch.filter(os.listdir('.'), '*-*.xlsx')

    for this_xlsx_filename in excel_files:
        print(f'Working on {this_xlsx_filename}',
              flush=True)

        # identify course
        this_course_id = this_xlsx_filename[this_xlsx_filename.find('.') + 1:this_xlsx_filename.find('.xlsx')]
        if args.debug:
            print(f'this_course_id:{this_course_id}',
                  file=sys.stderr)

        ##
        # read excel file contents
        try:
            this_xlsx = pandas.read_excel(this_xlsx_filename)
        except Exception as err:
            print(f'* Cannot read excel file [{this_xlsx_filename}]\n   {err}',
                  file=sys.stderr)
            continue

        ##
        # extract score from csv file
        if not args.comments_only:
            try:
                score = -1
                for row_ind in range(len(this_xlsx) - 1, -1, -1):
                    if this_xlsx.at[row_ind, list(this_xlsx)[0]] == score_label:
                        score = this_xlsx.at[row_ind, score_column]
                        if args.debug:
                            print(f'Score is {score}',
                                  flush=True)
                    if 'factor' in config.keys():
                        score = score * config['factor']
                assert (score != -1)
            except Exception as err:
                print(f'* Score not found for [{this_xlsx_filename}]\n   {err}\n'
                      f'Looking for column header "{score_column}" and row header "{score_label}"',
                      file=sys.stderr,
                      flush=True)
                continue

        ##
        # grab Canvas student ID from filename

        this_sid = this_xlsx_filename[re.search(r'\d', this_xlsx_filename).start():this_xlsx_filename.rfind('-')]
        if args.debug:
            print(f'**student_canvas_id: {this_sid}',
                  file=sys.stderr,
                  flush=True)

        if not args.comments_only:
            ##
            # First, try to upload the grade

            ##
            # find this student's submission
            assignment_entry = '**unassigned**'
            try:
                # noinspection PyUnboundLocalVariable
                this_submission_uri = f'{assignments_uri}/{assignment_id_map[course_id]}/submissions/{this_sid}'
                this_submission_response = requests.get(url=this_submission_uri,
                                                        headers=headers)
                assignment_entry = json.loads(this_submission_response.text)
            except Exception as err:
                if args.debug:
                    print(f'assignment_entry: {assignment_entry}',
                          file=sys.stderr,
                          flush=True)
                print(f'\n*** Could not find assignment entry for {this_xlsx_filename}\n   {err}\n',
                      file=sys.stderr,
                      flush=True)
                continue

            ##
            # Find assignment attempts
            submission_id = assignment_entry["id"]
            attempt = assignment_entry["attempt"]
            if args.debug:
                print(f'**submission_id: {submission_id}, attempt is {attempt}',
                      file=sys.stderr,
                      flush=True)
            if attempt is None:
                print(f'\n*** No attempts by this student {this_xlsx_filename}\n ',
                      file=sys.stderr,
                      flush=True)
                continue
            for this_attempt in range(1, attempt + 1):
                ##
                # Set all earlier attempts to 0 (to insure only one grade prevails
                # just in case use highest grade is set.
                # This is something people might want to change.
                # noinspection PyUnboundLocalVariable
                this_score = 0 if this_attempt < attempt else score
                this_score = float(this_score)

                ##
                # Set posted grade for this assignment
                submission_uri = f'{assignments_uri}/{assignment_id_map[course_id]}/submissions/{this_sid}'

                if args.debug:
                    print(f'**submission_uri {submission_uri}\n  headers={headers}',
                          file=sys.stderr,
                          flush=True)
                if not args.n:
                    params = {'submission[posted_grade]': str(this_score)}
                    try:
                        response = requests.put(url=submission_uri,
                                                headers=headers,
                                                params=params)
                        if this_attempt == attempt:
                            if args.debug:
                                print(f'request: {submission_uri}:{params}')
                            print(f'  Uploaded grade {this_score} for {this_xlsx_filename}',
                                  flush=True)
                    except Exception as err:
                        # noinspection PyUnboundLocalVariable
                        print(f'**http request failed {request_uri}\nresponse: {response.text}\n   {err}',
                              file=sys.stderr,
                              flush=True)
                else:
                    if this_attempt == attempt:
                        print(f'***No action for {this_xlsx_filename}, score: {this_score}',
                              flush=True)

        ##
        # Now upload excel comments
        comment_upload_uri =  f"{assignments_uri}/{assignment_id_map[course_id]}/submissions/{this_sid}"

        if args.debug:
            print(f'**comment_upload_uri: {comment_upload_uri}',
                  file=sys.stderr,
                  flush=True)

        if not args.n:
            try:
                # Use Canvas REST API file upload procedure:
                # 1. Request an upload url
                # 2. Use the upload url to upload the file
                # 3. Confirm the upload
                # 4. Set the comment

                ##
                # 1. Request upload url
                try:
                    upload_rq_params = {'name': this_xlsx_filename,
                                        'size': str(os.stat(this_xlsx_filename).st_size),
                                        'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                        'on_duplicate': 'overwrite'}
                    upload_rq_uri = \
                        f'{comment_upload_uri}/comments/files/'
                    upload_rq_response = requests.post(url=upload_rq_uri,
                                                       headers=headers,
                                                       params=upload_rq_params)
                    if args.debug:
                        print(f'* Request upload url response: {upload_rq_response.text}')
                except Exception as err:
                    # noinspection PyUnboundLocalVariable
                    print(f'* Request upload url failed: {upload_rq_response.text}\n   {err}',
                          file=sys.stderr,
                          flush=True)

                try:
                    ##
                    # 2. Upload file to specified url
                    upload_rq = json.loads(upload_rq_response.text)
                    upload_uri = upload_rq['upload_url']
                    do_upload_response = requests.post(url=upload_uri,
                                                       params=upload_rq['upload_params'],
                                                       files={'file': open(this_xlsx_filename, 'rb')})
                except Exception as err:
                    # noinspection PyUnboundLocalVariable
                    print(f'* upload failed, uri:{upload_uri}\n' +
                          f'upload_response is {do_upload_response.text}\n    {err}',
                          file=sys.stderr,
                          flush=True)
                    #print('* upload failed', file=sys.stderr, flush=True)
                do_upload = json.loads(do_upload_response.text)
                if args.debug:
                    print(f'do_upload response: {do_upload}',
                          file=sys.stderr)

                ##
                # 3. Confirm upload (2 options: one for 201 response, another for 3XX response)
                if do_upload_response.status_code == 201:
                    confirmation_response = requests.post(url=do_upload['location'],
                                                          headers=headers,
                                                          params={'Content-Length': '0'})
                else:
                    assert int(do_upload_response.status_code / 100) == 3, 'Erroneous status code from upload'
                    confirmation_response = requests.get(url=do_upload['location'])
                if args.debug:
                    print(f'confirmation response is {confirmation_response.text}',
                          file=sys.stderr,
                          flush=True)

                ##
                # 4. Set the comment
                confirmation = json.loads(confirmation_response.text)
                comment_addfile = requests.put(url=comment_upload_uri,
                                               headers=headers,
                                               params={'comment[file_ids][]': f'{str(confirmation["id"])}'})
                if args.debug:
                    print(f'comment_addfile " {comment_addfile.text}',
                          file=sys.stderr,
                          flush=True)

            except Exception as err:
                print(f'* Excel comment file upload failed]\n   {err}',
                      file=sys.stderr,
                      flush=True)



    if args.n:
        print('No upload actions actually performed',
              flush=True)


if __name__ == '__main__':
    main()
