import os
import shutil
import gitlab
from git import Repo
from gitea import *
import sys
import re
from urllib.parse import urlparse
import argparse
import time
from students import Students
from server_interaction import ServerInteractions

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
parser.add_argument('-c', '--choice', type=str, default=None, help="Server Choice between gitlab and gitea", required=True) #added in order to request the server to work with and mantain the compatibility with both servers


args = parser.parse_args()


xlsx_path = args.input

try:
    students = Students(xlsx_path)
except Exception as e:
    print(e)
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

server_choice = args.choice.lower() 
# taking the server choice to make the entire script conditional
# in every case will be run a single script because the whole script is conditional based on the server given when calling the script

server = ServerInteractions(server_choice)

gitlab_delay=args.gitlab_delay

num_existing_users = 0
users = server.get_users()
username_pattern = re.compile("^"+prefix_username+"(\d+)$")

for user in users:

	if username_pattern.match(user.username):
		user_num = int(re.search(r'\d+$', user.username).group())
		if user_num > num_existing_users:
			num_existing_users = user_num

print("Existing students in GitLab: " + str(num_existing_users))


num_students = students.get_num_students()
print("Total students: " + str(num_students))


print("Populating XLSX with usernames/passwords...")
students.initialize_users(prefix_username, num_existing_users + 1, password_length, top_project_group, project_subgroup)


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



for student in students:

	username = student["username"]
	password = student["password"]
	fullname = student["surname"] + " " + student["firstname"]
	email = username + "@example.com"


	new_user = True
	new_project = True

	try:
		user = server.create_user([username, password, fullname, email])
		print(f"New user '{username}' (full name: {fullname}, pass: {password})")
		time.sleep(gitlab_delay)

	except:
		user = server.get_user(username)
		print(f"Retrieved existing user '{username}'")
		new_user = False


	project_name = username

	try:
		project = server.create_project(project_name, group, project_subgroup)

		print(f"New project '{project_name}' created")

		time.sleep(gitlab_delay)

		server.add_member(group, project_name, username)

		print(f"Push access for user '{username}' to project '{project_name}'")

		#https://stackoverflow.com/questions/67794798/how-to-update-a-protected-branch-in-python-gitlab
		server.protect_main_branch(group, project_name, username)

		print(f"Push access for branch 'main' to project '{project_name}'")

		time.sleep(gitlab_delay)

	except Exception as e:
		print(e)
		project = server.get_project(group, project_name)
		print(f"Retrieving existing project '{project_name}'")
		new_project = False

	if server_choice == "gitlab":
		project_remote_path = f"{server.get_url()}/{top_project_group}/{project_subgroup}/{project_name}"
	elif server_choice == "gitea":
		project_remote_path = f"{server.get_url()}/{top_project_group}/{project_name}"
		# apparently the project subgroup is not needed to access the repo in gitea
		
	project_local_path = os.path.join(local_path,project_name)

	repository_url = f"https://{username}:{password}@{project_remote_path}"

	students.set_repository_url(student["row"], repository_url)


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

