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
import numpy as np
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError

TOKEN = ''
mainPath = "/opt/data/archive/"

#0 for windows 1 for linux
os_test = 0

listOfFiles = list()
if os_test == 0:
    for (dirpath, dirnames, filenames) in os.walk("./dados"):
        listOfFiles += [os.path.join(dirpath, file)[1:] for file in filenames]
if os_test == 1:
    for (dirpath, dirnames, filenames) in os.walk(mainPath):
        listOfFiles += [os.path.join(dirpath, file) for file in filenames if dirpath.startswith(mainPath)]
    
days = [int(i.split('.')[-1]) for i in listOfFiles]
days = np.array(days)
oldMax = max(days)

daysCheck = np.where((oldMax - days) > 300, days + 366, days)

maxVal = max(daysCheck)
indices = [i for i, x in enumerate(daysCheck) if x == maxVal]

for i  in reversed(indices):
    del listOfFiles[i]

if os_test == 0:
    listOfFiles = [w.replace(mainPath, '/') for w in listOfFiles]

for lista in listOfFiles:
    print(lista)

dbx = dropbox.Dropbox(TOKEN, timeout = 90)

try:
    dbx.users_get_current_account()
except AuthError:
    sys.exit("ERROR: Invalid access token; try re-generating an "
        "access token from the app console on the web.")

print()
print()

CHUNK_SIZE = 1 * 1024 * 1024

for file in listOfFiles:
    meta = None
    os_path = file
    if os_test == 0:
        os_path = "." + file
    file_size = os.path.getsize(os_path)
    try:
        meta = dbx.files_get_metadata(file.replace(mainPath, '/'))
        print("arquivo existe!") 
    except:
        print("arquivo não existe!")
#    with open("." + file, 'rb') as f:
    with open(os_path, 'rb') as f:
#        if meta == None or meta.size != file_size:
        if meta == None or meta.size != os.path.getsize(os_path):
            print("arquivo diferente, fazendo a sincronização!")
            print()
            if file_size <= CHUNK_SIZE:
                try:
                    dbx.files_upload(f.read(), os_path.replace(mainPath, '/'), mode=WriteMode('overwrite'))
    #                dbx.files_upload(f.read(), file.replace(mainPath, '/'), mode=WriteMode('overwrite'))
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
                upload_session_start_result = dbx.files_upload_session_start(f.read(CHUNK_SIZE))
                cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id,
                                               offset=f.tell())
                commit = dropbox.files.CommitInfo(path=os_path.replace(mainPath, '/'))
                
                while f.tell() < file_size:
                    if ((file_size - f.tell()) <= CHUNK_SIZE):
                        print (dbx.files_upload_session_finish(f.read(CHUNK_SIZE),
                                            cursor, commit))
                    else:
                        dbx.files_upload_session_append(f.read(CHUNK_SIZE),
                                            cursor.session_id, cursor.offset)
                        cursor.offset = f.tell()
        else:
            print(meta.size)
            os.path.getsize(os_path)
            print()
