#! /bin/sh -x
#
# grade_assignment.sh
#
# Assumes directory contains downloaded canvas assignment pdf file with filenames of form
#    lastname_firstnameXXXXXX_question_######_#######_assignmentname.pdf
# and .xlsx grading spreadsheets with filenames of form
#    lastname_firstnameXXXXXX:YYYYYY.xlsx
# where XXXXXX is the Canvas Student ID and
# YYYYYY is the Canvas Course Shell ID
#
# successively an xlsx spreadsheet and the pdf file for a student.
# When grading for a student is complete, close these files and press return in the shell
# where grade_assignment.sh was run.
#
# After grading an asignment use submit_assignment.py to submit grades to canvas
#

for x in *.xlsx; do
    pdf=${x/:*/}
    pdf=*$pdf*.pdf
    open $pdf
    open "$x"
    read
    done
    
