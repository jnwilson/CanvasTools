# CanvasTools
This repo contains tools to automate grading and submission of grades for student assignments associated with Canvas LMS courses.
0. Things we hope you do only once:

   A. Place copy_rubric.py, grade_assignment.sh, and submit_assignment.py
      into a directory in your PATH variable.

   B. Create a grading_directory and cd into it.

   C. Place your Canvas API_Token in the grading_directory

1. Things you do for each assignment you grade:

   A. Create an assignment subdirectory (e.g. Ex###) and cd to it

   B. Copy the config file and rubric xlsx file into that assignment
      subdirectory and cd into it.

   C. Open the rubric xlsx file and make sure the position and size are
      what you want them to be for grading the entire assignment.
      If your using a Mac (and possibly other systems) every copy will
      open in the same locaion with the same size.
      Best to get it correct right off the bat.

   D. Make sure you are cd'd to the assignment directory.
   
   D. Execute copy_rubric.py

   E. Open a web browser.
      Navigate to the Canvas course shell and get to the Assignment page for
      the assignment you are grading and click the "Download Submissions"
      link on the right side of the page.
      After the submissions zip file downloads, unzip it in your local
      assignment directory.

      Execute grade_assignment.sh

      Now, for each assignment, click to open the student's pdf submission.
      Verify that the name of the xlsx file matches the student's name.
      Fill out the xlsx file appropriately.
      Save the xlsx file and *QUIT* Excel.
        (On a Mac, that means using Cmd-Q.
         If you use Cmd-W to just close the window, the script will not
     open the next file.)

      I have tested the grade_assignment.sh script on Mac.
      I think it probably works on Linux.
      It works in WSL on Windows.
      If you fix it to work somewhere else, tell me and I'll update it.

   F. When you've done that for every student, execute

      submit_assignment.sh

      ***NOTE*** You may want to test that in a subdirectory that has
      just a single student's xlsx file in it.
      It posts comments to each student's assignment.
      If you did something wrong and need to redo this, you will
      have to delete the comments that were uploaded by hand.
      I do not know of a way to remove those comments with the API.
      If you find such a way and create a script to do it properly,
      I'll include that in these procedures.

      flags:
      -n: Do a dry run--Don't actually upload the comments but tell
          each student's score that would be uploaded
      -debug: Provide whatever ridiculous debug messages I was using
          when I debugged this most recently.


Tips:

0. Open your pdf reader on a document and open the rubric xlsx file.
   Size and position them for convenient grading before you get started
   and before you copy the rubric.
   This will help you avoid having to resize windows every time to start
   grading a new assignment.

1. If you are using Acrobat reader on Windows and the All Tools pane
   is on the left every time you start reading a document, this tells
   how to modify that behavior:
   https://helpx.adobe.com/acrobat/kb/disable-right-hand-pane-in-acrobat-reader.html#:~:text=To%20hide%20the%20All%20tools,Select%20OK.