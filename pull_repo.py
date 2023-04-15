import os
import shutil
import gitlab
from git import Repo
import xlwings as xw
import sys
import argparse
from urllib.parse import urlparse
import time
from students import Students


import requests
requests.packages.urllib3.disable_warnings()


parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', help="Path to XLSX with list of students", required=True)
parser.add_argument('-r', '--repo', help="Folder for local repos", required=True)

args = parser.parse_args()


xlsx_path = args.input

try:
    students = Students(xlsx_path)
except Exception as e:
    print(e)
    sys.exit(1)


local_path = args.repo

if not (os.path.exists(local_path) and os.path.isdir(local_path)):
    print(f"Error: '{local_path}' is not a valid folder")
    sys.exit(1)


num_students = students.get_num_students()
print("Total students: " + str(num_students))




for student in students:

    username = student["username"]
    password = student["password"]
    fullname = student["surname"] + " " + student["firstname"]
    repository_url = student["repository_url"]

    if username is None:
        print("Error: Missing username in XLSX")
        sys.exit(1)

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

