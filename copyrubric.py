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
        student_file = open(args.students,'r')
    except:
        sys.stderr.write('Unable to open student file: [' + args.students + ']\n')
        sys.stderr.write('Exception info: ' + str(sys.exc_info()[0]))
        exit(1)

    student_list = student_file.readlines()
    for entry in student_list:
        new_filename = entry.rstrip() + '.xlsx'
        try:
            shutil.copy2(args.rubric, new_filename)
            print(new_filename.rstrip())
        except:
            sys.stderr.write('Unable to create xlsx file for [' + new_filename + ']\n')
            sys.stderr.write('Exception info: ' + str(sys.exc_info()) + '\n')

if __name__ == '__main__':
    main()
