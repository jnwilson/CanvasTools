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

#!!! Possibly delete commas from filenames for the benefit of WSL

for x in *_*-*.xlsx; do
    cmp $x rubric*.xlsx >/dev/null
    if [ $? != 0 ]; then continue; fi
    base=${x/%-*}
    base1=${base/_*/}    
    base2=${base/*_/}
    # get just 1 pdf file name in $pdf in case there are extras
    pdf=`ls $base1*$base2*.pdf`
    pdf=${pdf/pdf*/pdf}
    #for pdf in `ls $base1*$base2*.pdf`; do break; done
    if [ -e "$pdf" ]; then $Opener "$pdf"; \
    else if [ -e "$base1*$base2*.docx" ]; then $Opener "$base1*$base2*.docx"; fi; fi
    $Opener "$x"
    read
    done
    
