import os
import sys
import shutil
import gitlab
from git import Repo
import argparse
from urllib.parse import urlparse
from students_db import StudentsDB
from server_interaction import ServerInteractions

import requests
requests.packages.urllib3.disable_warnings()


parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
#group.add_argument('-i', '--input', help="Path to XLSX with list of students")
group.add_argument('-s', '--subgroup', help="Subgroup")
group.add_argument('-u', '--user', help="Git platform user")
parser.add_argument('-g', '--group', default="so", help="Top-level group")
parser.add_argument('-p', '--pull', action='store_true', default=False, help="Enable clone/pull of most recent commit")
parser.add_argument('-r', '--repo', help="Folder for local repos")
parser.add_argument('-n', '--rename', action='store_true', default=False, help="Rename project folder using surname/firstname")
parser.add_argument('-b', '--git-platform', default="gitea", help="Git platform, either 'gitlab' or 'gitea'")

args = parser.parse_args()


#xlsx_path = args.input


if args.pull is True and args.repo is None:
    print(f"Error: for cloning/pulling the repos, a path to local folder must be provided (-r)")
    sys.exit(1)

pull_enabled = args.pull
rename_projects = args.rename
local_path = args.repo


top_project_group = args.group
project_subgroup = args.subgroup
selected_user = args.user

#if selected_user is None and project_subgroup is None and xlsx_path is None:
#    print("Error: you need to specify an XLSX (-i) or a group/subgroup (-g, -s) or a user (-u)")
#    sys.exit(1)

if selected_user is None and project_subgroup is None:
    print("Error: you need to specify a group/subgroup (-g, -s) or a user (-u)")
    sys.exit(1)


git_platform = args.git_platform.lower()

if not git_platform == 'gitlab' and not git_platform == 'gitea':
    print(f"Error: '{git_platform}' is not valid (should be either 'gitlab' or 'gitea')")
    sys.exit(1)

server = ServerInteractions(git_platform)


projects = []
credentials = {}


'''
# Search projects using list from XLSX

if xlsx_path is not None:

    try:
        students = Students(xlsx_path)
    except Exception as e:
        print(e)
        sys.exit(1)

    num_students = students.get_num_students()
    print("Total students: " + str(num_students))


    for student in students:

        username = student["username"]
        password = student["password"]
        repository_url = student["repository_url"]

        project_name = username

        try:
            group = server.get_group(top_project_group)
            project = server.get_project(group, project_name)
        except:
            print(f"Project '{project_name}' not found, skipping...")
            continue

        projects.append(server.parse_project(project))

        credentials[username] = password
'''

try:
    students = StudentsDB()
except Exception as e:
    print(e)
    sys.exit(1)

#num_students = students.get_num_students()
#print("Total students: " + str(num_students))


for student in students:

    username = student["username"]
    password = student["password"]
    repository_url = student["repository_url"]

    credentials[username] = password

    # Search projects for all users

    if selected_user is None and project_subgroup is None:

        project_name = username

        try:
            group = server.get_group(top_project_group)
            project = server.get_project(group, project_name)
        except:
            print(f"Project '{project_name}' not found, skipping...")
            continue

        projects.append(server.parse_project(project))


# Search project using username

if selected_user is not None:

    project_name = selected_user

    try:
        group = server.get_group(top_project_group)
        project = server.get_project(group, project_name)
    except:
        print(f"Error: Project '{project_name}' not found")
        sys.exit(1)

    projects.append(server.parse_project(project))




# Search projects within group/subgroup

if project_subgroup is not None:

    try:
        group = server.get_group(top_project_group)
    except:
        print("Error: Top-level group not found")
        sys.exit(1)

    try:
        subgroup = server.get_subgroup(group, project_subgroup)
    except Exception as e:
        print(e)
        print("Error: Sub-group not found")
        sys.exit(1)

    for project in server.get_projects(top_project_group, project_subgroup):

        projects.append(server.parse_project(project))



for project in projects:

    try:
        commit = server.get_last_commit(project)
    except Exception as e:
        if e.args[0] == "'NoneType' object has no attribute 'username'":
            print("\tProbably there hasn't been a commit yet...")
        else:
            print(f"Project '{project.name}' not found, skipping...")



    if pull_enabled is True:

        project_name = project.name

        project_local_path = os.path.join(local_path,project_name)

        project_local_path_studentname = None


        if rename_projects:

            student_info = students.get_user_info(project_name)
            #print(student_info)

            if student_info["activated"] and (not student_info["surname"] is None) and (not student_info["firstname"] is None) and (not student_info["matricola"] is None):

                project_local_path_studentname = os.path.join(local_path, f"{student_info['surname'].lower()}-{student_info['firstname'].lower()}-{student_info['matricola']}")


                if os.path.exists(project_local_path):

                    os.rename(project_local_path, project_local_path_studentname)


                project_local_path = project_local_path_studentname



        if os.path.exists(project_local_path):

            print(f"Pulling local repo for '{project_name}'")

            repo = Repo(project_local_path)

            origin = repo.remotes.origin

            origin.pull(env={'GIT_SSL_NO_VERIFY': '1'})

        else:

            #if xlsx_path is None:
            #    print(f"Unable to clone repo '{project_name}' (only supported with XLSX list with users/passwords)")
            #    continue

            username = project_name
            password = credentials[username]
            project_remote_path = server.get_clone_url(project)
            protocol = server.get_protocol()

            repository_url = f"{protocol}://{username}:{password}@{project_remote_path}"

            print(f"Cloning from {repository_url}")

            repo = Repo.clone_from(repository_url, project_local_path, env={'GIT_SSL_NO_VERIFY': '1'})



