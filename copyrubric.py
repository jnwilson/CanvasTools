#! /usr/bin/env python3

import sys
import argparse
import shutil


def main():
    parser = argparse.ArgumentParser(description='Copy Rubric to student files')
    parser.add_argument('--students',
                        help='file containing student names and Canvs ID (comma separated)',
                        default='../student-file')

    parser.add_argument('--rubric',
                        help="rubric xlsx file for assignment",
                        default='rubric.xlsx')

    args = parser.parse_args()

    ##
    # read student file
    try:
        student_file = open(args.students, 'r')
    except Exception as err:
        print(f'Unable to open student file: [{args.students}]: {str(err)}',
              file=sys.stderr,
              flush=True)
        exit(1)

    # noinspection PyUnboundLocalVariable
    student_list = student_file.readlines()
    for entry in student_list:
        new_filename = entry.rstrip() + '.xlsx'
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
