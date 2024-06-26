import os
import shutil
import gitlab
from git import Repo
import gitea
import sys
import re
from urllib.parse import urlparse
import argparse
import time
from students_db import StudentsDB
from server_interaction import ServerInteractions

import requests
requests.packages.urllib3.disable_warnings()


parser = argparse.ArgumentParser()
parser.add_argument('-x', '--xlsx-import', help="Path to XLSX with list of students")
parser.add_argument('-n', '--number-of-accounts', type=int, help="Number of new accounts to create")
parser.add_argument('-g', '--group', default="so", help="Top-level group")
parser.add_argument('-s', '--subgroup', help="Subgroup", required=True)
parser.add_argument('-r', '--repo', help="Folder where to create local repos")
parser.add_argument('-f', '--ref', help="Folder with reference code", required=True)
parser.add_argument('-p', '--prefix', default="student-", help="Prefix for student repos")
parser.add_argument('-l', '--password-length', type=int, default=8, help="Length for randomly-generated passwords")
parser.add_argument('-d', '--api-delay', type=int, default=1, help="Delay (in seconds) between API calls")
parser.add_argument('-b', '--git-platform', type=str, default="gitea", help="Git platform, either 'gitlab' or 'gitea'")


args = parser.parse_args()

xlsx_path = args.xlsx_import
number_of_accounts = args.number_of_accounts

if xlsx_path is None and number_of_accounts is None:
    print("fError: You should either specify the number of new accounts (-n) or an XLSX to list the accounts (-i)")
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

git_platform = args.git_platform.lower()

if not git_platform == 'gitlab' and not git_platform == 'gitea':
	print(f"Error: '{git_platform}' is not valid (should be either 'gitlab' or 'gitea')")
	sys.exit(1)

server = ServerInteractions(git_platform)

api_delay=args.api_delay

num_existing_users = 0
users = server.get_users()
username_pattern = re.compile("^"+prefix_username+"(\d+)$")

for user in users:

	if username_pattern.match(user.username):
		user_num = int(re.search(r'\d+$', user.username).group())
		if user_num > num_existing_users:
			num_existing_users = user_num

print(f"Existing students on server: " + str(num_existing_users))



students = StudentsDB()

if xlsx_path is not None:

	print(f"Importing accounts from {xlsx_path}...")

	try:
		students.import_users(xlsx_path, prefix_username, password_length, top_project_group, project_subgroup, num_existing_users+1)

		xlsx_num_students = students.xlsx_num_students
		print(f"Imported {xlsx_num_students} from XLSX")

	except Exception as e:
		print(f"Error: Failed initialization from XLSX file: {e}")
		sys.exit(1)

elif number_of_accounts is not None:

	print(f"Initializing {number_of_accounts} new accounts...")

	students.initialize_users(number_of_accounts, prefix_username, password_length, top_project_group, project_subgroup, num_existing_users+1)




try:
	group = server.get_group(top_project_group)
except:
	print("Top-level group not found, creating new one")
	group = server.create_group(top_project_group)

try:
	subgroup = server.get_subgroup(group, project_subgroup)
except:
	print("Sub-group not found, creating new one")
	subgroup = server.create_subgroup(group, project_subgroup)


if not ".gitignore" in os.listdir(reference_path):

    with open(os.path.join(reference_path, ".gitignore"), "w") as gitignore:

        gitignore.write("*.o\n")
        gitignore.write("*.pdf\n")
        gitignore.write("*~\n")

        if "Makefile" in os.listdir(reference_path):

            with open(os.path.join(reference_path, "Makefile")) as makefile:

                p = re.compile("^(\w+):")

                for line in makefile:

                    match = p.match(line)
                    
                    if match:

                        rulename = match.group(1)

                        if rulename != "all" and rulename != "clean":
                            
                            gitignore.write(rulename+"\n")



for student in students:

	if student["group"] != top_project_group or student["subgroup"] != project_subgroup:
		continue

	username = student["username"]
	password = student["password"]
	fullname = student["surname"] + " " + student["firstname"]
	email = username + "@example.com"


	new_user = True
	new_project = True

	try:
		user = server.create_user([username, password, fullname, email])
		print(f"New user '{username}' (full name: {fullname}, pass: {password})")
		time.sleep(api_delay)

	except:
		user = server.get_user(username)
		print(f"Retrieved existing user '{username}'")
		new_user = False


	project_name = username

	try:

		project = server.create_project(project_name, group, project_subgroup)

		print(f"New project '{project_name}' created")

		time.sleep(api_delay)

		server.add_member(group, project_name, project_subgroup, username)

		print(f"Push access for user '{username}' to project '{project_name}'")

		#https://stackoverflow.com/questions/67794798/how-to-update-a-protected-branch-in-python-gitlab
		server.protect_main_branch(group, project_name, username)

		print(f"Push access for branch 'main' to project '{project_name}'")

		time.sleep(api_delay)

	except Exception as e:
		print(e)
		project = server.get_project(group, project_name)
		print(f"Retrieving existing project '{project_name}'")
		new_project = False

	project_remote_path = server.get_clone_url(project)
	# apparently the project subgroup is not needed to access the repo in gitea

	project_local_path = os.path.join(local_path,project_name)

	protocol = server.get_protocol()
	repository_url = f"{protocol}://{username}:{password}@{project_remote_path}"

	students.set_repository_url(student["username"], repository_url)


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

