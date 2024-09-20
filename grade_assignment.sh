#! /usr/bin/bash
#
# grade_assignment.sh
#
# Assumes current directory contains .xlsx grading spreadsheets with filenames of form
#    lastname-firstname-XXXXXX-YYYYYY.xlsx
# where XXXXXX is the Canvas Student ID and
# YYYYYY is the Canvas Course Shell ID
#
# Use speed grader to access each student's record in turn
# The xlsx spreadsheet are opened successivly for each student in the
# Modify the student's .xlsx file to correctly reflect their grade.
# When grading for a student is complete, close the xlsx file
#  and proceed to the next student in speed grader
# ***MAKE SURE YOU HAVE THE XLSX FILE FOR THE RIGHT STUDENTS***
#
# After grading an asignment use submit_assignment.py to submit grades to canvas
#


Args=''
if [ -z $WSL_DISTRO_NAME ]; then
    if [ `uname` == Linux ]; then Opener=atril;
    elif [ `uname` == Darwin ]; then Opener="open" Args="-Wn";
    fi
else Opener="cmd.exe /c start";
fi


for x in *-*.xlsx; do
    cmp $x rubric*.xlsx >/dev/null
    if [ $? != 0 ]; then continue; fi
    base=${x%-*}
    base1=${base##*-}
    #echo base1 is $base1
    echo *$base1*.pdf
    $Opener *$base1*.pdf
    $Opener /wait $x
    read -p "Next? " y
    done
    
