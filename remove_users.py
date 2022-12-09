import os
import sys
import gitlab
import xlwings as xw
import argparse

import requests
requests.packages.urllib3.disable_warnings()

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', help="Path to XLSX with list of students", required=True)
args = parser.parse_args()

xlsx_path = args.input

if not os.path.exists(xlsx_path):
    print(f"Error: '{xlsx_path}' does not exist")
    sys.exit(1)

if not xlsx_path.endswith('.xlsx'):
    print(f"Error: '{xlsx_path}' does not seem an XLSX file")
    sys.exit(1)


if not os.path.exists('./python-gitlab.cfg'):
    print("Unable to find python-gitlab.cfg")
    sys.exit(1)

print("GitLab authentication")

config = gitlab.config.GitlabConfigParser(config_files=['./python-gitlab.cfg'])
gl = gitlab.Gitlab(config.url, private_token=config.private_token, keep_base_url=True, ssl_verify=False)

gl.auth()



wb = xw.Book(xlsx_path)
sheet = wb.sheets[0]


empty_column = sheet.used_range[-1].offset(column_offset=1).column

username_column = None

for col in range(1,empty_column):

    if sheet.range((1,col)).value == "username":
        username_column = col

if username_column is None:
    print("Username column not found in XLSX")
    sys.exit(1)


num_students = sheet.range('A1').end('down').row

print(f"This script will delete {num_students} students")
confirm = input("Do you want to continue [type 'yes']? ")

if confirm != "yes":
    print("Aborting on user request")
    sys.exit(0)


for row in range(2,num_students+1):

    username = sheet.range((row,username_column)).value

    try:
        user = gl.users.list(username=username)[0]
    except:
        print(f"User '{username}' not found, skipping")
        continue

    print(f"Deleting '{username}'...")

    gl.users.delete(user.id)
