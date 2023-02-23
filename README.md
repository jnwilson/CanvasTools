# CanvasTools
This repo contains tools to automate grading and submission of grades for student assignments associated with Canvas LMS courses.

Parenthetical remarks have to do with my normal usage
To grade assignments, you will need:

    rollfile (generated from a Canvas full Grades csv file download))
    rubric.xlsx (copied from rubric-###.xlsx into theassignment directory)
    student assignments (download from Canvas Quiz with
         "Download All Files" link)
    API_Token (generate from Canvas Account Settings page -- look for
        the big blue "+ New Access Token Button"
   config-### (config file as specified in submit_assignments.py))

1.  Directory hierarchy:

      Main Grading Directory (contains API_Token, config files, rollfile)
           Assignment-specific Subdirectory (contains downloaded
             student files, rubric-###.xlsx)

2. What to do:
    in Assignment-specific Subdirectory, run these commands:
      copy_rubric.py --rubric rubric-###.xlsx --rollfile ../rollfile
      grade_assignment.sh

3. To test upload
    Create a test directory in the Assignment-specific Subdirectory
    Copy one student.xlsx file into there
    In that directory (!!!) run this command:
      submit_assignments.py --config ../../config-### --token ../../API_Token
   Use speed grader to see that that student's grade has been updated.
   (It is best to set the Manual Posting setting for the course to hide the
    grades from the student's view while uploading in case there are problems.)

4. To do full upload
    cd into Assignment-Specific Subdirectory
    In that directory (!!!) run this command:
       submit_assignments.py --config ../config-### --token ../API_Token

5. Check student grades (probably all of them) and if they match, Rejoice

6. Unhide the assignment grades.