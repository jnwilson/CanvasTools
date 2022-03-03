#! /usr/bin/env bash
#
# grade_assignment.sh
#
# Assumes directory contains downloaded canvas assignment pdf file with filenames of form
#    lastnamefirstname_XXXXXX_question_######_#######_assignmentname.pdf
# and .xlsx grading spreadsheets with filenames of form
#    lastnamefirstname_XXXXXX:YYYYYY.xlsx
# where XXXXXX is the Canvas Student ID and
# YYYYYY is the Canvas Course Shell ID
#
# successively an xlsx spreadsheet and the pdf file for a student.
# When grading for a student is complete, close these files and press return in the shell
# where grade_assignment.sh was run.
#
# After grading an asignment use submit_assignment.py to submit grades to canvas
#

Opener=open
if [ `uname` == Linux ]; then Opener=xdg-open; fi

for x in *_*:*.xlsx; do
    cmp $x rubric.xlsx >/dev/null
    if [ $? != 0 ]; then continue; fi
    base=${x/:*/}
    pdf=$base*.pdf
    if [ -e $base*.pdf ]; then $Opener $base*.pdf; \
    else if [ -e $base$.docx ]; then $Opener $base*.docx; fi; fi
    $Opener "$x"
    read
    done
    
