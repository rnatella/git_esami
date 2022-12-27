import os
import sys
import gitlab
import argparse
from students import Students

import requests
requests.packages.urllib3.disable_warnings()

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', help="Path to XLSX with list of students", required=True)
args = parser.parse_args()

xlsx_path = args.input

try:
    students = Students(xlsx_path)
except Exception as e:
    print(e)
    sys.exit(1)



if not os.path.exists('./python-gitlab.cfg'):
    print("Unable to find python-gitlab.cfg")
    sys.exit(1)

print("GitLab authentication")

config = gitlab.config.GitlabConfigParser(config_files=['./python-gitlab.cfg'])
gl = gitlab.Gitlab(config.url, private_token=config.private_token, keep_base_url=True, ssl_verify=False)

gl.auth()



num_students = students.get_num_students()

print(f"This script will delete {num_students} students")
confirm = input("Do you want to continue [type 'yes']? ")

if confirm != "yes":
    print("Aborting on user request")
    sys.exit(0)


for student in students:

    username = student["username"]

    try:
        user = gl.users.list(username=username)[0]
    except:
        print(f"User '{username}' not found, skipping")
        continue

    print(f"Deleting '{username}'...")

    gl.users.delete(user.id)
