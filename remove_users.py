import os
import sys
import gitlab
import argparse
from students_db import StudentsDB
from server_interaction import ServerInteractions

import requests
requests.packages.urllib3.disable_warnings()

parser = argparse.ArgumentParser()
#parser.add_argument('-i', '--input', help="Path to XLSX with list of students", required=True)
parser.add_argument('-b', '--git-platform', default="gitea", help="Git platform, either 'gitlab' or 'gitea'")

args = parser.parse_args()

#xlsx_path = args.input

#try:
#    students = Students(xlsx_path)
#except Exception as e:
#    print(e)
#    sys.exit(1)

try:
    students = StudentsDB()
except Exception as e:
    print(e)
    sys.exit(1)


git_platform = args.git_platform.lower()

if not git_platform == 'gitlab' and not git_platform == 'gitea':
    print(f"Error: '{git_platform}' is not valid (should be either 'gitlab' or 'gitea')")
    sys.exit(1)

server = ServerInteractions(git_platform)


num_students = students.get_num_students()

print(f"This script will delete {num_students} students")
confirm = input("Do you want to continue [type 'yes']? ")

if confirm != "yes":
    print("Aborting on user request")
    sys.exit(0)


for student in students:

    username = student["username"]

    try:
        user = server.get_user(username)
    except:
        print(f"User '{username}' not found, skipping")
        continue

    print(f"Deleting '{username}'...")


    server.delete_user(user)

