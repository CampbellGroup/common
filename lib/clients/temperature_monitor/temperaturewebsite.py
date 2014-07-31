#!/usr/bin/env  python                                                                                                                                                             
# Run the code with the two arguments posted by temperature.html

import cgi
import cgitb
import os

print "Content-type: text/html\n\n"
print '<header>'
print '<h1>Temperature Grapher</h1>'
print '</header>'


# This gets variables from the post method
form=cgi.FieldStorage()


# Get values and run
else:
    startTime = form["startTime"].value
    os.system("function call with arguments") # add pyhton tempscript.py sysargs
