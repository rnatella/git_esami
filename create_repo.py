import os
import shutil
import gitlab
from git import Repo
import xlwings as xw
import secrets
import string
import sys
import re
from urllib.parse import urlparse
import argparse
import time

import requests
requests.packages.urllib3.disable_warnings()


parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', help="Path to XLSX with list of students", required=True)
parser.add_argument('-g', '--group', default="so", help="Top-level GitLab group")
parser.add_argument('-s', '--subgroup', help="GitLab subgroup", required=True)
parser.add_argument('-r', '--repo', help="Folder where to create local repos")
parser.add_argument('-f', '--ref', help="Folder with reference code", required=True)
parser.add_argument('-p', '--prefix', default="student-", help="Prefix for student repos")
parser.add_argument('-l', '--password-length', type=int, default=8, help="Length for randomly-generated passwords")
parser.add_argument('-d', '--gitlab-delay', type=int, default=5, help="Delay (in seconds) between GitLab API calls")

args = parser.parse_args()


xlsx_path = args.input

if not os.path.exists(xlsx_path):
    print(f"Error: '{xlsx_path}' does not exist")
    sys.exit(1)

if not xlsx_path.endswith('.xlsx'):
    print(f"Error: '{xlsx_path}' does not seem an XLSX file")
    sys.exit(1)



top_project_group = args.group
project_subgroup = args.subgroup

local_path = args.repo
reference_path = args.ref

if not (os.path.exists(local_path) and os.path.isdir(local_path)):
    print(f"Error: '{local_path}' is not a valid folder")
    sys.exit(1)

if not (os.path.exists(reference_path) and os.path.isdir(reference_path)):
    print(f"Error: '{reference_path}' is not a valid folder")
    sys.exit(1)

prefix_username = args.prefix
password_length = args.password_length
alphabet = string.ascii_letters + string.digits


if not os.path.exists('./python-gitlab.cfg'):
    print("Unable to find python-gitlab.cfg")
    sys.exit(1)

print("GitLab authentication")

config = gitlab.config.GitlabConfigParser(config_files=['./python-gitlab.cfg'])
gl = gitlab.Gitlab(config.url, private_token=config.private_token, keep_base_url=True, ssl_verify=False)

gl.auth()


gitlab_url=config.url
gitlab_server=urlparse(gitlab_url).netloc

gitlab_delay=args.gitlab_delay

num_existing_users = 0
users = gl.users.list(get_all=True)
username_pattern = re.compile("^"+prefix_username+"(\d+)$")

for user in users:

    if username_pattern.match(user.username):
        user_num = int(re.search(r'\d+$', user.username).group())
        if user_num > num_existing_users:
            num_existing_users = user_num


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


if surname_column is None or name_column is None:
    print("Error: Missing name or surname columns in XLSX")
    sys.exit(0)

if username_column is None:

    print("Populating XLSX with usernames/passwords...")

    username_column = empty_column
    password_column = empty_column + 1
    group_column = empty_column + 2
    subgroup_column = empty_column + 3
    url_column = empty_column + 4

    sheet.range((1,username_column)).value = "username"
    sheet.range((1,username_column)).font.bold = True

    sheet.range((1,password_column)).value = "password"
    sheet.range((1,password_column)).font.bold = True

    sheet.range((1,group_column)).value = "group"
    sheet.range((1,group_column)).font.bold = True

    sheet.range((1,subgroup_column)).value = "subgroup"
    sheet.range((1,subgroup_column)).font.bold = True

    sheet.range((1,url_column)).value = "repository_url"
    sheet.range((1,url_column)).font.bold = True



for row in range(2,num_students+1):

    username = sheet.range((row,username_column)).value
    password = sheet.range((row,password_column)).value

    if username is None and password is None:

        username = prefix_username + str(num_existing_users + row - 1)

        password = ''.join(secrets.choice(alphabet) for i in range(password_length))

        print(f"Initializing user '{username}'")

        sheet.range((row,username_column)).value = username
        sheet.range((row,password_column)).value = password

        sheet.range((row,group_column)).value = top_project_group
        sheet.range((row,subgroup_column)).value = project_subgroup


try:
    group = gl.groups.list(search=top_project_group)[0]
except:
    print("Top-level group not found, creating new one")
    group = gl.groups.create({'name': top_project_group, 'path': top_project_group})

try:
    subgroup = group.subgroups.list(search=project_subgroup)[0]
except:
    print("Sub-group not found, creating new one")
    subgroup = gl.groups.create({'name': project_subgroup, 'path': project_subgroup, 'parent_id': group.id})



for row in range(2,num_students+1):

    username = sheet.range((row,username_column)).value
    password = sheet.range((row,password_column)).value
    email = username + "@example.com"
    fullname = sheet.range((row,surname_column)).value + " " + sheet.range((row,name_column)).value

    new_user = True
    new_project = True

    try:
        user = gl.users.create({'email': email,
                            'password': password,
                            'username': username,
                            'name': fullname,
                            'skip_confirmation': 'true'})

        print(f"New user '{username}' (full name: {fullname}, pass: {password})")

        time.sleep(gitlab_delay)

    except:
        user = gl.users.list(username=username)[0]
        print(f"Retrieved existing user '{username}'")
        new_user = False


    project_name = username

    try:
        project = gl.projects.create(
                        {'name': project_name,
                        'default_branch': 'main',
                        'initialize_with_readme': 'true',
                        'namespace_id': subgroup.id
                        })

        print(f"New project '{project_name}' created")

        time.sleep(gitlab_delay)

        member = project.members.create({'user_id': user.id, 'access_level':
                                        gitlab.const.AccessLevel.DEVELOPER})

        print(f"Push access for user '{username}' to project '{project_name}'")

        #https://stackoverflow.com/questions/67794798/how-to-update-a-protected-branch-in-python-gitlab
        project.protectedbranches.delete('main')
        project.protectedbranches.create({
                        'name': 'main',
                        'merge_access_level': gitlab.const.AccessLevel.DEVELOPER,
                        'push_access_level': gitlab.const.AccessLevel.DEVELOPER,
                        'allow_force_push': False
                    })

        print(f"Push access for branch 'main' to project '{project_name}'")

        time.sleep(gitlab_delay)

    except Exception as e:
        print(e)
        project = gl.projects.list(search=project_name)[0]
        print(f"Retrieving existing project '{project_name}'")
        new_project = False


    project_remote_path = f"{gitlab_server}/{top_project_group}/{project_subgroup}/{project_name}"
    project_local_path = os.path.join(local_path,project_name)

    repository_url = f"https://{username}:{password}@{project_remote_path}"
    sheet.range((row,url_column)).value = repository_url


    if os.path.exists(project_local_path) and new_project is True:
        print("Local repo already existing, removing old one...")
        shutil.rmtree(project_local_path)

    elif os.path.exists(project_local_path):
        print("Local repo already existing but no new repo, skipping...")
        continue


    print(f"Cloning: {repository_url}")

    repo = Repo.clone_from(repository_url, project_local_path, env={'GIT_SSL_NO_VERIFY': '1'})


    if os.path.exists(os.path.join(project_local_path, "README.md")):
        repo.index.remove(["README.md"], working_tree = True)

    # Copy all files from reference folder to local repo
    for file_name in os.listdir(reference_path):

        source = os.path.join(reference_path, file_name)
        destination = os.path.join(project_local_path, file_name)

        # copy only files
        if os.path.isfile(source):
            shutil.copy(source, destination)
            print('copied: ', file_name)
            repo.index.add([file_name])

    repo.index.commit("Initial commit")

    origin = repo.remote(name='origin')
    origin.push()

wb.close()