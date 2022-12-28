import os
import sys
import signal
import shutil
from urllib.parse import urlparse
import gitlab
from flask import Flask, request
import netifaces
import netaddr
import argparse
import logging
from time import monotonic
import asyncio
from threading import Thread
from datetime import datetime

import requests
requests.packages.urllib3.disable_warnings()

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, DataTable
from textual import events


def init_commits(students: dict, top_project_group: str, project_subgroup: str):

    projects = []

    # Search projects within group/subgroup

    if project_subgroup is not None:

        try:
            group = gl.groups.list(search=top_project_group)[0]
        except:
            print("Error: Top-level group not found")
            sys.exit(1)

        try:
            subgroup = group.subgroups.list(search=project_subgroup)[0]
        except:
            print("Error: Sub-group not found")
            sys.exit(1)

        for group_obj in gl.groups.get(subgroup.id).projects.list(all=True, order_by='name', sort='asc'):

            projects.append(gl.projects.get(group_obj.id))

    for project in projects:

        try:
            commit = project.commits.list(ref_name='main', get_all=False)[0]
            #print(f"{project.name}\t{commit.created_at}\t{commit.committer_name}\t\t{commit.message}")

        except:
            print(f"Error retrieving commit for project {project.name}")
            continue

        project_name = project.name
        timestamp = commit.created_at
        author = commit.committer_name
        commit = commit.message

        students[project_name] = {}
        students[project_name]["project"] = project_name
        students[project_name]["timestamp"] = timestamp
        students[project_name]["author"] = author
        students[project_name]["commit"] = commit
        students[project_name]["local_timestamp"] = 0




class DashboardApp(App):

    SORT_BY_NAME = 0
    SORT_BY_TIME = 1
    HIGHLIGHT_PERIOD = 10

    BINDINGS = [
        ("n", "sort_by_name", "Sort by name"),
        ("t", "sort_by_time", "Sort by time"),
        ("q", "quit", "Quit")
    ]

    CSS = """
    DataTable > .datatable--highlight {
        background: $surface;
    }
    """

    def init_students(self, students: dict):
        self.students = students

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield DataTable(show_header=True, show_cursor=False)


    def on_mount(self) -> None:

        self.sort_column = self.SORT_BY_NAME
        self.sort_order_reverse = False

        table = self.query_one(DataTable)

        table.add_column("Project")
        table.add_column("Time")
        table.add_column("Author")
        table.add_column("Commit")

        commits = self.list_commits()

        rows = iter(commits)
        table.add_rows(rows)

        self.set_interval(1, self.update_table)


    def update_table(self) -> None:
        table = self.query_one(DataTable)
        table.clear()

        commits = self.list_commits()

        rows = iter(commits)
        table.add_rows(rows)
        table.refresh()
    

    def list_commits(self) -> list:

        first_col_format = "[bold magenta]%s[/bold magenta]"
        col_format = "%s"

        first_col_format_highlight = "[bold magenta on yellow]%s[/bold magenta on yellow]"
        col_format_highlight = "[bold on yellow]%s[/bold on yellow]"

        mydata = sorted(
            [
                (
                    (first_col_format_highlight if (monotonic() - students[s]["local_timestamp"] < self.HIGHLIGHT_PERIOD) else first_col_format) % self.students[s]["project"],
                    (col_format_highlight if (monotonic() - students[s]["local_timestamp"] < self.HIGHLIGHT_PERIOD) else col_format) % datetime.fromisoformat(self.students[s]["timestamp"]).replace(tzinfo=None),
                    (col_format_highlight if (monotonic() - students[s]["local_timestamp"] < self.HIGHLIGHT_PERIOD) else col_format) % self.students[s]["author"],
                    (col_format_highlight if (monotonic() - students[s]["local_timestamp"] < self.HIGHLIGHT_PERIOD) else col_format) % self.students[s]["commit"]
                )
                for s in self.students
            ],
            key=lambda x: x[self.sort_column],
            reverse=self.sort_order_reverse,
        )

        return mydata

    def action_sort_by_name(self) -> None:
        self.sort_column = self.SORT_BY_NAME
        self.sort_order_reverse = False
        self.update_table()
    
    def action_sort_by_time(self) -> None:
        self.sort_column = self.SORT_BY_TIME
        self.sort_order_reverse = True
        self.update_table()

    def action_quit(self) -> None:
        self.exit()

    def exit(self):
        hook.delete()
        super().exit()




def flask_loop(loop, HOOK_PATH: str, HOOK_PORT: int, students: dict) -> None:

    app = Flask(__name__)

    asyncio.set_event_loop(loop)

    @app.route(HOOK_PATH, methods=['POST'])
    def webhook():
        if request.method == 'POST':

            #print("Data received from Webhook is: ", request.json)

            content = request.get_json()

            if "object_kind" in content and content["object_kind"] == "push":

                project_name = content["project"]["name"]

                for commit in content["commits"]:

                    commit_created_at = commit["timestamp"]
                    commit_committer_name = commit["author"]["name"]
                    commit_message = commit["message"]

                    students[project_name]["project"] = project_name
                    students[project_name]["timestamp"] = commit_created_at
                    students[project_name]["author"] = commit_committer_name
                    students[project_name]["commit"] = commit_message
                    students[project_name]["local_timestamp"] = monotonic()

            return "OK!"


    log = logging.getLogger('werkzeug')
    #log.setLevel(logging.ERROR)
    log.disabled = True

    app.run(host='0.0.0.0', port=HOOK_PORT)



if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--group', default="so", help="Top-level GitLab group")
    parser.add_argument('-s', '--subgroup', nargs='+', help="GitLab subgroup(s)", required=True)
    parser.add_argument('-p', '--webhook_port', default=8000, type=int, help="Webhook port")
    parser.add_argument('-w', '--webhook_path', default="/webhook", help="Webhook path")

    args = parser.parse_args()

    HOOK_PATH = args.webhook_path
    HOOK_PORT = args.webhook_port

    top_project_group = args.group
    project_subgroups = args.subgroup

    if not os.path.isabs(HOOK_PATH):
        print(f"Error: '{HOOK_PATH}' is not a valid absolute URL path")
        sys.exit(1)



    if not os.path.exists('./python-gitlab.cfg'):
        print("Unable to find python-gitlab.cfg")
        sys.exit(1)

    print("GitLab authentication")

    config = gitlab.config.GitlabConfigParser(config_files=['./python-gitlab.cfg'])
    gl = gitlab.Gitlab(config.url, private_token=config.private_token, keep_base_url=True, ssl_verify=False)

    gl.auth()


    gitlab_url=config.url
    gitlab_server=urlparse(gitlab_url).netloc


    webhook_server_addr = None


    if netaddr.valid_ipv4(gitlab_server):

        # Look for local network interface on this machine
        # that matches the GitLab server IP (e.g., a local virtual machine)

        # https://stackoverflow.com/questions/3755863/trying-to-use-my-subnet-address-in-python-code

        for iface in netifaces.interfaces():

            addrs = netifaces.ifaddresses(iface)

            if netifaces.AF_INET in addrs.keys():
                
                for addr in addrs[netifaces.AF_INET]:
                    
                    ip = addr["addr"]
                    netmask = addr["netmask"]

                    cidr = netaddr.IPNetwork('%s/%s' % (ip, netmask))

                    ipset = netaddr.IPSet([cidr])


                    if gitlab_server in ipset:
                        print(f"GitLab IP '{gitlab_server}' match found for IP address '{ip}' on interface '{iface}', subnet '{cidr.network}/{cidr.prefixlen}'")
                        webhook_server_addr = ip
                        break


    if webhook_server_addr is None:
        print("GitLab server address is not a local IP address.")
        print("Tunnel not yet implemented, quitting")
        sys.exit(0)


    students = {}

    for project_subgroup in project_subgroups:
        print(f"Retrieving data for group /{top_project_group}/{project_subgroup}")
        init_commits(students, top_project_group, project_subgroup)


    webhook_url = f'http://{webhook_server_addr}:{HOOK_PORT}{HOOK_PATH}'

    print(f"Initializing hook at: {webhook_url}")

    hook = gl.hooks.create({
                            'url': webhook_url,
                            'push_events': True
                        })


    loop = asyncio.new_event_loop()
    t = Thread(target=flask_loop, args=(loop, HOOK_PATH, HOOK_PORT, students,), daemon=True)
    t.start()

    try:
        app = DashboardApp()
        app.init_students(students)
        app.run()
    except KeyboardInterrupt:
        print("Bye!")



