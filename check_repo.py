import os
import sys
import shutil
import gitlab
import xlwings as xw
import argparse

import requests
requests.packages.urllib3.disable_warnings()


parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', help="Path to XLSX with list of students", required=True)
parser.add_argument('-g', '--group', default="so", help="Top-level GitLab group")
parser.add_argument('-s', '--subgroup', help="GitLab subgroup", required=True)
parser.add_argument('-u', '--user', help="GitLab user")

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

selected_user = args.user

print("GitLab authentication")

config = gitlab.config.GitlabConfigParser(config_files=['./python-gitlab.cfg'])
gl = gitlab.Gitlab(config.url, private_token=config.private_token, keep_base_url=True, ssl_verify=False)

gl.auth()



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
    fullname = sheet.range((row,surname_column)).value + " " + sheet.range((row,name_column)).value

    if selected_user is not None and username != selected_user:
        continue

    q_project_name = f"{top_project_group}/{project_subgroup}/{username}"

    try:
        project = gl.projects.get(q_project_name)

        commit = project.commits.list(ref_name='main')[0]
        print(f"{username}\t{commit.created_at}\t{commit.committer_name}\t{commit.message}")
    except:
        print(f"Project '{q_project_name}' not found, skipping...")

