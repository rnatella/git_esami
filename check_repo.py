import os
import sys
import shutil
import gitlab
from git import Repo
import xlwings as xw
import argparse

import requests
requests.packages.urllib3.disable_warnings()


parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument('-i', '--input', help="Path to XLSX with list of students")
group.add_argument('-s', '--subgroup', help="GitLab subgroup")
group.add_argument('-u', '--user', help="GitLab user")
parser.add_argument('-g', '--group', default="so", help="Top-level GitLab group")
parser.add_argument('-p', '--pull', action='store_true', default=False, help="Enable clone/pull of most recent commit")
parser.add_argument('-r', '--repo', help="Folder for local repos")

args = parser.parse_args()


xlsx_path = args.input

if xlsx_path is not None and not os.path.exists(xlsx_path):
    print(f"Error: '{xlsx_path}' does not exist")
    sys.exit(1)

if xlsx_path is not None and not xlsx_path.endswith('.xlsx'):
    print(f"Error: '{xlsx_path}' does not seem an XLSX file")
    sys.exit(1)


if args.pull is True and args.repo is None:
    print(f"Error: for cloning/pulling the repos, a path to local folder must be provided (-r)")
    sys.exit(1)

pull_enabled = args.pull
local_path = args.repo


top_project_group = args.group
project_subgroup = args.subgroup

selected_user = args.user


if selected_user is None and project_subgroup is None and xlsx_path is None:
    print("Error: you need to specify an XLSX (-i) or a GitLab group/subgroup (-g, -s) or a GitLab user (-u)")
    sys.exit(1)

#if bool(top_project_group is None) != bool(project_subgroup is None):
#    print("Error: the GitLab group and subgroup (-g, -s) should be both set to a value")
#    sys.exit(1)



print("GitLab authentication")

config = gitlab.config.GitlabConfigParser(config_files=['./python-gitlab.cfg'])
gl = gitlab.Gitlab(config.url, private_token=config.private_token, keep_base_url=True, ssl_verify=False)

gl.auth()


projects = []


# Search projects using list from XLSX

if xlsx_path is not None:

    wb = xw.Book(xlsx_path)
    sheet = wb.sheets[0]

    empty_column = sheet.used_range[-1].offset(column_offset=1).column

    username_column = None
    password_column = None
    url_column = None
    surname_column = None
    name_column = None

    for col in range(1,empty_column):

        if sheet.range((1,col)).value == "username":
            username_column = col

        if sheet.range((1,col)).value == "password":
            password_column = col

        if sheet.range((1,col)).value == "repository_url":
            url_column = col

        if sheet.range((1,col)).value.casefold() == "cognome":
            surname_column = col

        if sheet.range((1,col)).value.casefold() == "nome":
            name_column = col

    if username_column is None:
        print("Error: 'username' column not found in XLSX file")
        sys.exit(1)

    num_students = sheet.range('A1').end('down').row
    print("Total students: " + str(num_students))


    for row in range(2,num_students+1):

        username = sheet.range((row,username_column)).value
        password = sheet.range((row,password_column)).value
        repository_url = sheet.range((row,url_column)).value
        
        project_name = username

        try:
            project = gl.projects.list(search=project_name, order_by='name', sort='asc')[0]
        except:
            print(f"Project '{project_name}' not found, skipping...")
            continue

        projects.append(project)

    wb.close()

  


# Search project using username

if selected_user is not None:

    project_name = selected_user

    try:
        project = gl.projects.list(search=project_name, order_by='name', sort='asc')[0]
    except:
        print(f"Error: Project '{project_name}' not found")
        sys.exit(1)

    projects.append(project)




# Search projects within group/subgroup

if project_subgroup is not None:

    try:
        group = gl.groups.list(search=top_project_group)[0]
    except:
        print("Error: Top-level group not found")
        sys.exit(1)

    try:
        subgroup = group.subgroups.list(search=project_subgroup)[0]
    except:
        print("Error: Sub-group not found")
        sys.exit(1)

    for group_obj in gl.groups.get(subgroup.id).projects.list(all=True, order_by='name', sort='asc'):

        projects.append(gl.projects.get(group_obj.id))



for project in projects:

    try:

        commit = project.commits.list(ref_name='main')[0]
        print(f"{project.name}\t{commit.created_at}\t{commit.committer_name}\t\t{commit.message}")

    except:
        print(f"Project '{project.name}' not found, skipping...")
    
    

    if pull_enabled is True:

        if repository_url is None:
            print(f"Empty repository URL for user '{username}', skipping...")

        project_name = username

        project_local_path = os.path.join(local_path,project_name)

        if os.path.exists(project_local_path):

            print(f"Pulling local repo for '{username}'")

            repo = Repo(project_local_path)

            origin = repo.remotes.origin

            origin.pull(env={'GIT_SSL_NO_VERIFY': '1'})

        else:

            print(f"Cloning from {repository_url}")

            repo = Repo.clone_from(repository_url, project_local_path, env={'GIT_SSL_NO_VERIFY': '1'})
