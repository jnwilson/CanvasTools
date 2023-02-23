#! /usr/bin/env python3
# noinspection SpellCheckingInspection
"""
copyrubric.py

Assumptions:
  0. You use the Canvas LMS for a class or several classes you are teaching or assisting with.
  1. The current directory where you are running this is a grades directory.
  2. You have a grading rubric .xlsx file (preferably in some other directory).
  3. You have a rollfile each \n separated line of which is of form lastname_firstnameXXXXX:YYYYY
     (where XXXXX is Canvas Student ID and YYYYY is Canvas Course ID)
     for every student in the class or classes for which you are grading.
"""

import sys
import argparse
import shutil


def main():
    parser = argparse.ArgumentParser(description='Copy Rubric to student files')
    parser.add_argument('--rollfile',
                        help='file containing lname_fnameXXXX:YYYY where XXXX is Student ID and YYYY is Course ID',
                        default='../rollfile')

    parser.add_argument('--rubric',
                        help="rubric xlsx file for assignment",
                        default='rubric.xlsx')
    parser.add_argument('--separator',
                        help='separator to use between SIS and course number',
                        default='-')
    
    args = parser.parse_args()

    ##
    # read student file
    try:
        with open(args.rollfile, 'r') as f:
            student_list = f.readlines()
            f.close()
    except Exception as err:
        print(f'Unable to open roll file: [{args.rollfile}]: {str(err)}',
              file=sys.stderr,
              flush=True)
        exit(1)

    # noinspection PyUnboundLocalVariable
    for entry in student_list:
        colon_index = entry.find(':')
        new_filename = entry[:colon_index] + args.separator + entry[colon_index+1:].rstrip() + '.xlsx'
        try:
            shutil.copy2(args.rubric, new_filename)
            print(new_filename.rstrip())
        except Exception as err:
            print(f'Unable to create xlsx file for [{new_filename}]: {str(err)}',
                  file=sys.stderr,
                  flush=True)
            exit(1)


if __name__ == '__main__':
    main()
