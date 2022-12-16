import os
import shutil
import gitlab
from git import Repo
import xlwings as xw
import sys
import argparse
from urllib.parse import urlparse
import time

import requests
requests.packages.urllib3.disable_warnings()


parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', help="Path to XLSX with list of students", required=True)
parser.add_argument('-r', '--repo', help="Folder for local repos", required=True)

args = parser.parse_args()


xlsx_path = args.input

if not os.path.exists(xlsx_path):
    print(f"Error: '{xlsx_path}' does not exist")
    sys.exit(1)

if not xlsx_path.endswith('.xlsx'):
    print(f"Error: '{xlsx_path}' does not seem an XLSX file")
    sys.exit(1)

local_path = args.repo

if not (os.path.exists(local_path) and os.path.isdir(local_path)):
    print(f"Error: '{local_path}' is not a valid folder")
    sys.exit(1)



wb = xw.Book(xlsx_path)
sheet = wb.sheets[0]


empty_column = sheet.used_range[-1].offset(column_offset=1).column

username_column = None
password_column = None
url_column = None
group_column = None
subgroup_column = None
surname_column = None
name_column = None

for col in range(1,empty_column):

    if sheet.range((1,col)).value == "username":
        username_column = col

    if sheet.range((1,col)).value == "password":
        password_column = col

    if sheet.range((1,col)).value == "repository_url":
        url_column = col

    if sheet.range((1,col)).value == "group":
        group_column = col

    if sheet.range((1,col)).value == "subgroup":
        subgroup_column = col

    if sheet.range((1,col)).value.casefold() == "cognome":
        surname_column = col

    if sheet.range((1,col)).value.casefold() == "nome":
        name_column = col

num_students = sheet.range('A1').end('down').row
print("Total students: " + str(num_students))


if username_column is None:
    print("Error: Missing username column in XLSX")
    sys.exit(0)

if url_column is None:
    print("Error: Missing repository URL column in XLSX")
    sys.exit(0)



for row in range(2,num_students+1):

    username = sheet.range((row,username_column)).value
    password = sheet.range((row,password_column)).value
    fullname = sheet.range((row,surname_column)).value + " " + sheet.range((row,name_column)).value
    repository_url = sheet.range((row,url_column)).value

    if repository_url is None:
        print(f"Empty repository URL for user '{username}', skipping...")


    project_name = username
    project_local_path = os.path.join(local_path,project_name)
    repo = None

    if os.path.exists(project_local_path):

        print(f"Local repo for '{username}' already exists, pulling...")

        repo = Repo(project_local_path)

        origin = repo.remotes.origin

        origin.pull(env={'GIT_SSL_NO_VERIFY': '1'})

    else:

        print(f"Cloning: {repository_url}")

        repo = Repo.clone_from(repository_url, project_local_path, env={'GIT_SSL_NO_VERIFY': '1'})

    headcommit = repo.head.commit
    print(f"{username}\t{time.asctime(time.gmtime(headcommit.committed_date))}\t{headcommit.author.name}\t{headcommit.message}")


wb.close()