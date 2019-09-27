# -*- coding: utf-8 -*-
"""
Created on Thu Sep 26 09:09:42 2019

This code will upload the entire structure on archive folder from Raspberry Shake
he will verify the existence of the files, compare the sizes, and if not exists or different,
will upload the miniSeed file to dropbox

use Python 3 to run the code, and tne official dropbox python library.
to automate the process you can make an entry on crontab on the raspberry shake.
a dropbox token is necessary to make it work.

I`m not very good with python and sorry for the slopy code.
please feel free to make any suggestion.

@author: Pablo Pizutti
"""

import sys
import os
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError

TOKEN = ''
mainPath = "/opt/data/archive/"

######get a list of the files on mainPath, and remove the current day, current day file still in progress an not complete
listOfFiles = list()
#for (dirpath, dirnames, filenames) in os.walk("."):
#    listOfFiles += [os.path.join(dirpath, file)[1:] for file in filenames if dirpath.startswith(".\\")]
for (dirpath, dirnames, filenames) in os.walk(mainPath):
    listOfFiles += [os.path.join(dirpath, file) for file in filenames if dirpath.startswith(mainPath)]
    
days = [int(i.split('.')[-1]) for i in listOfFiles]

daysCheck = days.copy()
for day in daysCheck:
    if day <10:
        daysCheck[daysCheck == day] += 366

maxVal = max(daysCheck)
indices = [i for i, x in enumerate(daysCheck) if x == maxVal]

for i  in reversed(indices):
    del listOfFiles[i]

#listOfFiles = [w.replace(mainPath, '/') for w in listOfFiles]

for lista in listOfFiles:
    print(lista)

######Start the dropbox process
dbx = dropbox.Dropbox(TOKEN)

try:
    dbx.users_get_current_account()
except AuthError:
    sys.exit("ERROR: Invalid access token; try re-generating an "
        "access token from the app console on the web.")

print()
print()

for file in listOfFiles:
    meta = None
    try:
        meta = dbx.files_get_metadata(file.replace(mainPath, '/'))
        print("File already exists!") 
    except:
        print("File not uploaded!")
#    with open("." + file, 'rb') as f:
    with open(file, 'rb') as f:
#        if meta == None or meta.size != os.path.getsize("." + file):
        if meta == None or meta.size != os.path.getsize(file):
            try:
                dbx.files_upload(f.read(), file.replace(mainPath, '/'), mode=WriteMode('overwrite'))
            except ApiError as err:
                # This checks for the specific error where a user doesn't have enough Dropbox space quota to upload this file
                if (err.error.is_path() and
                        err.error.get_path().error.is_insufficient_space()):
                    sys.exit("ERROR: Cannot back up; insufficient space.")
                elif err.user_message_text:
                    print(err.user_message_text)
                    sys.exit()
                else:
                    print(err)
                    sys.exit()
        else:
            print(meta.size)
            print(os.path.getsize(file))
            print()
