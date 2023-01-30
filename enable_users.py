import gitlab
from gitea import *
import os
import sys
import argparse
from urllib.parse import urlparse
from server_interaction import ServerInteractions

import requests
requests.packages.urllib3.disable_warnings()

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument("-e", "--enable", action=argparse.BooleanOptionalAction, help="Enable push permissions")
group.add_argument("-d", "--disable", action=argparse.BooleanOptionalAction, help="Disable push permissions")
parser.add_argument("-g", '--group', default="so", help="Top-level GitLab group")
parser.add_argument("-s", '--subgroup', help="GitLab subgroup", required=True)
parser.add_argument("-c", '--choice', help="Server Choice", required = True)

args = parser.parse_args()

if args.enable is True:
    action = "enable"
elif args.disable is True:
    action = "disable"
else:
    print("Error: Specify either --enable or --disable")
    sys.exit(1)



top_project_group = args.group
project_subgroup = args.subgroup
project_path='/'+top_project_group+'/'+project_subgroup
server_choice = args.choice.lower()

server = ServerInteractions(server_choice)

subgroup_projects = server.get_projects(top_project_group, project_subgroup)

for project in subgroup_projects:

	member = server.get_member(project)
	server.edit_member_access(member, action, project)

