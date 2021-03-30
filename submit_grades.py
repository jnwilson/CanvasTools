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
        json dictionary with entries course_id and quiz_id

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
    comment_response = None
    config = None
    response = None
    score_column = 'Deductions'

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
    #  "exercise_name": "Ex210:Nonexistent Exercise",
    #  "score_column": "Total",
    #  "course_id": 3482356,
    #  "quiz_id": 03823646}

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

    ##
    # read score column from config
    if 'score_column' in config.keys():
        score_column = config["score_column"]

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

    quiz_uri = 'https://ufl.instructure.com/api/v1/courses/' + \
        str(config['course_id']) + '/quizzes/' + \
        str(config['quiz_id'])

    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer ' + access_token.rstrip()}

    ##
    # get info on quiz questions
    questions_uri = quiz_uri + '/questions'

    questions_response = requests.get(url=questions_uri,
                                      headers=headers,
                                      params={'per_page': '500'})

    Only_one_question = False
    questions = json.loads(questions_response.text)
    question_0 = questions[0]["id"]
    try:
        question_1 = questions[1]["id"]
    except:
        Only_one_question = True


    ##
    # get quiz submissions
    submissions_uri = quiz_uri + '/submissions'

    submissions_response = requests.get(url=submissions_uri,
                                        headers=headers,
                                        params={'per_page': '500'})

    submissions = json.loads(submissions_response.text)['quiz_submissions']

    ##
    # find assignment id
    assignments_uri = 'https://ufl.instructure.com/api/v1/courses/' + \
                      str(config['course_id']) + '/assignments/'
    assignments_response = requests.get(url=assignments_uri,
                                        headers=headers,
                                        params={'per_page': '500'})
    assignments = json.loads(assignments_response.text)
    try:
        if args.debug:
            print(f'config["quiz_id"] is {config["quiz_id"]}',
                  flush=True)
        asst_entry = list(filter(lambda x: 'quiz_id' in x and x['quiz_id'] == config['quiz_id'], assignments))
        assignment_id = asst_entry[0]["id"]
    except Exception as err:
        print(f'* Could not find assignment for quiz {config["quiz_id"]}\n   {str(err)}',
              file=sys.stderr,
              flush=True)
        exit(254)

    ##
    # Get verification of correct exercise

    exercise_name = asst_entry[0]['name']
    config_name = config['exercise_name']
    if not args.force:
        if input(f'\nExercise name is: {exercise_name}\nConfigured name:  '
                 f'{config_name}\n\nDo you want to continue? [y/n] ') != 'y':
            exit(1)

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
            this_csv_filename = this_xlsx_filename.replace('.xlsx', '.csv')
            this_xlsx.to_csv(this_csv_filename, index=None, header=True)
            this_csv_file = open(this_csv_filename, 'r')
            comment = this_csv_file.read()
            this_csv_file.close()
        except Exception as err:
            print(f'* Cannot make csv file for [{this_xlsx_filename}]\n   {str(err)}',
                  file=sys.stderr)
            continue

        if args.debug:
            print(f'**processing {this_csv_filename}',
                  flush=True)

        ##
        # extract score from csv file
        try:
            score = -1
            for row_ind in range(len(this_xlsx)-1, -1, -1):
                if this_xlsx.at[row_ind, list(this_xlsx)[0]] == 'Score':
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
        # upload comments
        comment_upload_uri = '{0}{1}/submissions/{2}'.format(assignments_uri, str(assignment_id),
                                                             str(student_canvas_id))
        if args.debug:
            print(f'**comment_upload_uri: {comment_upload_uri}',
                  flush=True)
            print(f'**comment[text_comment]: {comment}',
                  flush=True)

        if not args.n:
            try:
                comment_response = requests.put(url=comment_upload_uri,
                                                headers=headers,
                                                params={'comment[text_comment]': comment})
            except Exception as err:
                print(f'* Could not attach comment [{comment_response.text}]\n   {str(err)}',
                      file=sys.stderr,
                      flush=True)
                continue

        ##
        # find student id in submissions
        try:
            quiz_entry = list(filter(lambda x: 'user_id' in x and x['user_id'] == int(student_canvas_id), submissions))
            last_entry = quiz_entry[-1]
        except Exception as err:
            print(f'* Could not find quiz entry for {this_xlsx_filename}\n   {str(err)}',
                  file=sys.stderr,
                  flush=True)
            continue

        submission_id = last_entry["id"]
        attempt = last_entry["attempt"]
        if args.debug:
            print(f'**submission_id: {str(submission_id)}, attempt is {str(attempt)}',
                  flush=True)

        ##
        # post grade
        for this_attempt in range(1, attempt+1):
            # Set all earlier attempts to 0 (to insure only one grade prevails
            # just in case use highest grade is set.
            # This is something people might want to change.
            this_score = 0 if this_attempt < attempt else score
            this_score = float(this_score)

            if Only_one_question:
                json_arg = \
                    {"quiz_submissions": [{"attempt": this_attempt, "fudge_points": None,
                                           "questions": {str(question_0): {"score": this_score, "comment": None}}}]}
            else:
                json_arg = \
                    {"quiz_submissions": [{"attempt": this_attempt, "fudge_points": None,
                                           "questions": {str(question_0): {"score": this_score, "comment": None},
                                                         str(question_1): {"score": 0, "comment": None}}}]}

            request_uri = submissions_uri + '/' + str(submission_id)

            if args.debug:
                print(f'**request_uri {request_uri}\n**arg: {json_arg}',
                      flush=True)
                print(f'headers={headers}',
                      flush=True)
            if not args.n:
                try:
                    response = requests.put(url=request_uri,
                                            json=json_arg,
                                            headers=headers)
                    if this_attempt == attempt:
                        print(f'Uploaded grade for {this_xlsx_filename}',
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
