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

import requests
requests.packages.urllib3.disable_warnings()


parser = argparse.ArgumentParser()
parser.add_argument('-g', '--group', default="so", help="Top-level GitLab group")
parser.add_argument('-s', '--subgroup', nargs='+', help="GitLab subgroup(s)", required=True)
parser.add_argument('-p', '--webhook_port', default=8000, type=int, help="Webhook port")
parser.add_argument('-w', '--webhook_path', default="/webhook", help="Webhook path")

args = parser.parse_args()

HOOK_PATH = args.webhook_path
HOOK_PORT = args.webhook_port

if not os.path.isabs(HOOK_PATH):
    print(f"Error: '{HOOK_PATH}' is not a valid absolute URL path")
    sys.exit(1)


app = Flask(__name__)

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

                print(f"{project_name}\t{commit_created_at}\t{commit_committer_name}\t\t{commit_message}")

        return "OK!"


def close_webhook(signal, frame):

    print("\nDeleting hook")
    hook.delete()
    sys.exit(0)

signal.signal(signal.SIGINT, close_webhook)
signal.signal(signal.SIGTERM, close_webhook)


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


webhook_url = f'http://{webhook_server_addr}:{HOOK_PORT}{HOOK_PATH}'

print(f"Initializing hook at: {webhook_url}")

hook = gl.hooks.create({
                        'url': webhook_url,
                        'push_events': True
                    })

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app.run(host='0.0.0.0', port=HOOK_PORT)
