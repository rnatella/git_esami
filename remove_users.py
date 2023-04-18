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
parser.add_argument("-g", '--group', default="so", help="Top-level group")
parser.add_argument("-s", '--subgroup', help="Subgroup", required=True)
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



top_project_group = args.group
project_subgroup = args.subgroup
project_path='/'+top_project_group+'/'+project_subgroup


subgroup_projects = server.get_projects(top_project_group, project_subgroup)

users = []
repos = []

for project in subgroup_projects:
    repos.append(project)
    users.append(server.get_member(project))


print(f"This script will delete {len(users)} students")
confirm = input("Do you want to continue [type 'yes']? ")

if confirm != "yes":
    print("Aborting on user request")
    sys.exit(0)

for repo in repos:

    print(f"Deleting '{repo}'...")

    server.delete_repo(repo)


for user in users:

    username = server.get_username(user)

    print(f"Deleting '{username}'...")

    server.delete_user(user)

    students.delete_user(username)

