#! /usr/bin/env python3

import argparse
import csv
import codecs


def main():
    # set up arguments
    parser = argparse.ArgumentParser('Create Grading Roll')
    parser.add_argument('--csvfile',
                        required=True,
                        help='path to Canvas grading csv file')
    parser.add_argument('--course_id',
                        required=True,
                        help='Canvas Course ID (usually a 6-digit number)')
    parser.add_argument('-n',
                        action='store_true',
                        help='dry-run')
    args = parser.parse_args()

    # read account info csv file
    csv_file = codecs.open(args.csvfile, 'r')
    reader = csv.reader(csv_file)

    # skip headers
    next(reader)
    next(reader)
    next(reader)

    # send account email to each user in csv file
    for row in reader:
        raw_name = row[0]
        processed_name = raw_name.lower().replace(', ', '_')
        processed_name = processed_name.replace(' ', '_')
        processed_name = processed_name + row[1] + ':' + args.course_id
        print(processed_name)

    csv_file.close()


if __name__ == "__main__":
    main()