import gitlab
import os
import sys
import argparse
from urllib.parse import urlparse

import requests
requests.packages.urllib3.disable_warnings()

parser = argparse.ArgumentParser()
group = parser.add_mutually_exclusive_group()
group.add_argument("-e", "--enable", action=argparse.BooleanOptionalAction, help="Enable push permissions")
group.add_argument("-d", "--disable", action=argparse.BooleanOptionalAction, help="Disable push permissions")
parser.add_argument("-g", '--group', default="so", help="Top-level GitLab group")
parser.add_argument("-s", '--subgroup', help="GitLab subgroup", required=True)

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



if not os.path.exists('./python-gitlab.cfg'):
    print("Unable to find python-gitlab.cfg")
    sys.exit(1)

print("GitLab authentication")

config = gitlab.config.GitlabConfigParser(config_files=['./python-gitlab.cfg'])
gl = gitlab.Gitlab(config.url, private_token=config.private_token, keep_base_url=True, ssl_verify=False)

gl.auth()

gitlab_url=config.url
gitlab_server=urlparse(gitlab_url).netloc



group = gl.groups.list(search=top_project_group)[0]
subgroup = gl.groups.get(group.subgroups.list(search=project_subgroup)[0].id)

subgroup_projects = subgroup.projects.list(all=True)

for project in subgroup_projects:

    project = gl.projects.get(project.id)

    member = project.members.list(query=project.name)[0]

    if action == "disable":
        member.access_level = gitlab.const.AccessLevel.GUEST

    elif action == "enable":
        member.access_level = gitlab.const.AccessLevel.DEVELOPER

    member.save()