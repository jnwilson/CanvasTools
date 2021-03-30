#! /usr/bin/env python3
#

import sys
import pandas
from itertools import chain

filepath = 'SortGrades.csv'
try:
    this_csv = pandas.read_csv(filepath)
except Exception as err:
    print(f'**Could not open file {filepath}: {str(err)}',
          file=sys.stderr,
          flush=True)
    exit(-1)

#for index in range(77,128):
for index in chain(range(134,158), range(2,76)):
    # get student row

    new_df = pandas.DataFrame(this_csv.iloc[index]).T
    student_name = new_df.iloc[0]["Student"].replace(',', '')
    print(f'Working on {student_name}')


    # add new row with score line (to report cumulative grade)
    num_elts = len(new_df.iloc[0].values.tolist())
    x = ['']*num_elts
    x[0] = 'Score'
    x[3] = new_df.iloc[0]['Cum. Score']
    new_df.loc[len(new_df.index)]=x

    # write to excel file for studen
    new_df.to_excel(f'{student_name},{new_df.iloc[0]["ID"]}.xlsx',
                       index=False)


