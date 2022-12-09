import os
import shutil
import gitlab
from git import Repo
import xlwings as xw
import secrets
import string
import sys
import re

import requests
requests.packages.urllib3.disable_warnings()

#gitlab_server='172.16.190.143'
gitlab_server='172.16.73.132'
gitlab_url=f"https://{gitlab_server}"

top_project_group='so'
project_subgroup = 'test-123'
project_path='/'+top_project_group+'/'+project_subgroup


local_path  = "./testrepo/"
reference_path = "./testrepo/reference"

prefix_username = "student-"
password_length = 8
alphabet = string.ascii_letters + string.digits


print("GitLab authentication")

gl = gitlab.Gitlab(gitlab_url, private_token=os.getenv('GITLAB_PRIVATE_TOKEN'), keep_base_url=True, ssl_verify=False)
gl.auth()

num_existing_users = 0
users = gl.users.list(get_all=True)
username_pattern = re.compile("^"+prefix_username+"(\d+)$")

for user in users:

    if username_pattern.match(user.username):
        user_num = int(re.search(r'\d+$', user.username).group())
        if user_num > num_existing_users:
            num_existing_users = user_num


wb = xw.Book('/Users/rnatella/Downloads/studenti.xlsx')
sheet = wb.sheets[0]


empty_column = sheet.used_range[-1].offset(column_offset=1).column

username_column = None
password_column = None
surname_column = None
name_column = None

for col in range(1,empty_column):

    if sheet.range((1,col)).value == "username":
        username_column = col

    if sheet.range((1,col)).value == "password":
        password_column = col

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

    sheet.range((1,username_column)).value = "username"
    sheet.range((1,username_column)).font.bold = True

    sheet.range((1,password_column)).value = "password"
    sheet.range((1,password_column)).font.bold = True


    for row in range(2,num_students+1):

        password = ''.join(secrets.choice(alphabet) for i in range(password_length))

        sheet.range((row,username_column)).value = prefix_username + str(num_existing_users + row - 1)
        sheet.range((row,password_column)).value = password




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

    print(f"Creating user '{username}' (full name: {fullname}, pass: {password})")

    try:
        user = gl.users.create({'email': email,
                            'password': password,
                            'username': username,
                            'name': fullname,
                            'skip_confirmation': 'true'})
    except:
        user = gl.users.list(username=username)[0]

    project_name = username

    """Create Project of the new Repository"""
    try:
        project = gl.projects.create(
                        {'name': project_name,
                        'default_branch': 'main',
                        'initialize_with_readme': 'true',
                        'namespace_id': subgroup.id
                        })

        member = project.members.create({'user_id': user.id, 'access_level':
                                        gitlab.const.AccessLevel.DEVELOPER})

        #https://stackoverflow.com/questions/67794798/how-to-update-a-protected-branch-in-python-gitlab
        project.protectedbranches.delete('main')
        project.protectedbranches.create({
                        'name': 'main',
                        'merge_access_level': gitlab.const.AccessLevel.DEVELOPER,
                        'push_access_level': gitlab.const.AccessLevel.DEVELOPER,
                        'allow_force_push': False
                    })
    except:
        project = gl.projects.list(search=project_name)[0]


    project_remote_path = f"{project_path}/{project_name}"
    project_local_path = os.path.join(local_path,project_name)


    print(f"Cloning: {gitlab_server}:{project_remote_path}")

    clone = f"https://{username}:{password}@{gitlab_server}/{project_remote_path}" 
    repo = Repo.clone_from(clone, project_local_path, env={'GIT_SSL_NO_VERIFY': '1'})


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

    #repo = Repo.clone_from(gitlab_url, '/root/prova')
    #cloned_repo = repo.clone(os.path.join("./testrepo", "myrepo/"))