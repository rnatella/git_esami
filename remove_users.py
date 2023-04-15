import os
import sys
import gitlab
import argparse
from students import Students
from server_interaction import ServerInteractions

import requests
requests.packages.urllib3.disable_warnings()

parser = argparse.ArgumentParser()
parser.add_argument('-i', '--input', help="Path to XLSX with list of students", required=True)
parser.add_argument('-c', '--choice', help="Server Choice", required = True)

args = parser.parse_args()

xlsx_path = args.input
server_choice = args.choice

try:
    students = Students(xlsx_path)
except Exception as e:
    print(e)
    sys.exit(1)


server = ServerInteractions(server_choice)


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
