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
parser.add_argument("-g", '--group', default="so", help="Top-level group")
parser.add_argument("-s", '--subgroup', help="Subgroup", required=True)
parser.add_argument("-b", '--git-platform', default="gitea", help="Git platform, either 'gitlab' or 'gitea'")

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

git_platform = args.git_platform.lower()

if not git_platform == 'gitlab' and not git_platform == 'gitea':
    print(f"Error: '{git_platform}' is not valid (should be either 'gitlab' or 'gitea')")
    sys.exit(1)

server = ServerInteractions(git_platform)


subgroup_projects = server.get_projects(top_project_group, project_subgroup)

for project in subgroup_projects:

	member = server.get_member(project)
	server.edit_member_access(member, action, project)

