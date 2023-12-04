import os
import shutil
import gitlab
from git import Repo
import tomli
import gitea
import sys
import re
from urllib.parse import urlparse
from typing import Union, Dict


class ServerInteractions:

	def __init__(self, server_choice : str):
		if server_choice == "gitlab":

			if not os.path.exists('./python-gitlab.cfg'):
				print("Unable to find python-gitlab.cfg")
				sys.exit(1)


			print("GitLab authentication")

			config = gitlab.config.GitlabConfigParser(config_files=['./python-gitlab.cfg'])
			self.server = gitlab.Gitlab(config.url, private_token=config.private_token, keep_base_url=True, ssl_verify=False)

			self.server.auth()
			parsed_url = urlparse(config.url)
			self.server_url= parsed_url.netloc
			self.protocol = parsed_url.scheme


		elif server_choice == "gitea":

			if not os.path.exists('./gitea.toml'):
				print('Unable to find gitea.toml')
				sys.exit(1)


			with open('./gitea.toml', mode="rb") as f:
				cfg = tomli.load(f)

			self.server = gitea.Gitea(gitea_url = cfg['local']['url'],
				token_text=cfg['local']['token'],
				verify=False)

			parsed_url = urlparse(cfg['local']['url'])
			self.server_url = parsed_url.netloc
			self.server_hostname = parsed_url.hostname
			self.protocol = parsed_url.scheme


		self.server_choice = server_choice


	def get_url(self):
		return self.server_url

	def get_hostname(self):
		return self.server_hostname

	def get_protocol(self):
		return self.protocol


	def get_clone_url(self, project: Union[gitea.Repository, any]) -> str:

		if self.server_choice == "gitlab":
			return f"{self.server_url}/{project.path_with_namespace}"

		elif self.server_choice == "gitea":
			parsed_url = urlparse(project.clone_url)
			scheme = "%s://" % parsed_url.scheme
			return parsed_url.geturl().replace(scheme, '', 1)


	def get_users(self) -> list[Union[gitea.User, any]]:

		if self.server_choice == "gitlab":
			return self.server.users.list(get_all=True)

		elif self.server_choice == "gitea":
			return self.server.get_users()



	def get_user(self, username: str) -> Union[gitea.User,any]:

		if self.server_choice == "gitlab":
			return self.server.users.list(username = username)[0]

		elif self.server_choice == "gitea":
			return gitea.User.request(self.server, username)


	def get_username(self, user: Union[gitea.User,any]) -> str:

		if self.server_choice == "gitlab":
			return user.id

		elif self.server_choice == "gitea":
			return user.username



	def get_group(self, group_name: str) -> Union[gitea.Organization, any]:

		if self.server_choice == "gitlab":
			return self.server.groups.list(search=group_name)[0]

		elif self.server_choice == "gitea":
			return gitea.Organization.request(self.server, group_name)



	def get_subgroup(self, top_group:Union[gitea.Organization,any], sub_name: str) -> Union[gitea.Team, any]:

		if self.server_choice == "gitlab":
			return top_group.subgroups.list(search=sub_name)[0]

		elif self.server_choice == "gitea":
			return top_group.get_team(sub_name)



	def create_group(self, group_name: str) -> Union[gitea.Organization, any]:

		if self.server_choice == "gitlab":
			return self.server.groups.create({'name': group_name, 'path': group_name})

		elif self.server_choice == "gitea":
			owner = gitea.User.request(self.server, "root") # query to get the server owner
			self.server.create_org(owner, group_name, group_name)
			return gitea.Organization.request(self.server, group_name)



	def create_subgroup(self, group: Union[gitea.Organization, any], sub_name: str) -> Union[gitea.Team, any]:

		if self.server_choice =="gitlab":
			return self.server.groups.create({'name': sub_name, 'path': sub_name, 'parent_id' : group.id})

		elif self.server_choice == "gitea":
			#self.server.create_team(group, sub_name)
			self.server.create_team(group, sub_name, permission='')#, units='repo.code')
			return self.get_subgroup(group, sub_name)



	def create_user(self, usr_info: list) -> Union[gitea.User, any]:
		# index 0 -> username
		# index 1 -> password
		# index 2 -> fullname
		# index 3 -> email

		if self.server_choice == "gitlab":
			return self.server.users.create({'email': usr_info[3],
		                        'password': usr_info[1],
		                        'username': usr_info[0],
		                        'name': usr_info[2],
		                        'skip_confirmation': 'true'})

		elif self.server_choice == "gitea":
			self.server.create_user(user_name = usr_info[0],
									password = usr_info[1],
									full_name = usr_info[2],
									email = usr_info[3],
									change_pw = False,
									send_notify = False)

			user = gitea.User.request(self.server, usr_info[0])

			#subgroup.add_user(user) #TBD!!!

			return user


	def create_project(self, project_name: str, group: Union[gitea.Organization, any], subgroup_name: str) -> Union[gitea.Repository, any]:

		subgroup = self.get_subgroup(group, subgroup_name)

		if self.server_choice == "gitlab":
			return self.server.projects.create(
		                    {'name': project_name,
		                    'default_branch': 'main',
		                    'initialize_with_readme': 'true',
		                    'namespace_id': subgroup.id
		                    })

		elif self.server_choice == "gitea":
			group.create_repo(repoName = project_name, private = True) # default_branch and readme inizialization are by default in the used module

			project = gitea.Repository.request(self.server, owner = group.name, name = project_name)

			subgroup.add_repo(group, project)

			return project



	def get_project(self, group: Union[gitea.Organization, any], project_name: str) -> Union[gitea.Repository, any]:

		if self.server_choice == "gitlab":
			return self.server.projects.list(search=project_name)[0]

		elif self.server_choice == "gitea":
			return group.get_repository(project_name)



	def get_projects(self, top_name: str, sub_name: str) -> list:

		if self.server_choice == "gitlab":
			group = self.server.groups.list(search = top_name)[0]
			subgroup = self.server.groups.get(group.subgroups.list(search=sub_name)[0].id)
			return subgroup.projects.list(all=True)

		elif self.server_choice == "gitea":
			group = gitea.Organization.request(self.server, top_name)
			subgroup = group.get_team(sub_name)
			return subgroup.get_repos()



	def add_member(self, group: Union[gitea.Organization, any], project_name: str, sub_name: str, username: str):

		user = self.get_user(username)
		project = self.get_project(group, project_name)

		if self.server_choice == "gitlab":
			member = project.members.create({'user_id': user.id, 'access_level':
		                                    gitlab.const.AccessLevel.DEVELOPER})

		elif self.server_choice == "gitea":
			#project.add_collaborator(user)
			url = f"/repos/{project.owner.username}/{project.name}/collaborators/{username}"
			self.server.requests_put(url, {"permission": "write"})

			subgroup = group.get_team(sub_name)
			subgroup.add_user(user)


	def protect_main_branch(self,group: Union[gitea.Organization,any], project_name: str, whitelist_usr:str):

		project = self.get_project(group, project_name)

		if self.server_choice == "gitlab":
			project.protectedbranches.delete('main')
			project.protectedbranches.create({
		                    'name': 'main',
		                    'merge_access_level': gitlab.const.AccessLevel.DEVELOPER,
		                    'push_access_level': gitlab.const.AccessLevel.DEVELOPER,
		                    'allow_force_push': False
		                })

		elif self.server_choice == "gitea":
			pass
			#project.add_branch_protections(data = {"branch_name":"master",
		    #										"enable_push":True,
		    #										"enable_merge_whitelist":True,
		    #										"merge_whitelist_usernames": [whitelist_usr]
		    #										})

			#url = f"/repos/{project.owner.username}/{project.name}/branch_protections"

			#self.server.requests_put(url, {"branch_name":"master",
			#								"enable_push":True,
			#								"enable_merge_whitelist":True,
			#								"merge_whitelist_usernames": [whitelist_usr]
			#								})





	def get_member(self, project: Union[gitea.Repository, any]) -> Union[gitea.User, any] :

		if self.server_choice == "gitlab":
			project = self.server.projects.get(project.id)
			return project.members.list(query=project.name)[0]

		elif self.server_choice == "gitea":
			server_owner = gitea.User.request(self.server, "root")
			users = project.get_users_with_access()
			for usr in users:
				if usr != server_owner:
					return usr #doing this because for some reason users[0] is "out of range"



	def edit_member_access(self, usr : Union[gitea.User, any], action: str, repo: gitea.Repository) -> None:

		if self.server_choice == "gitlab":
			if action == "disable":
				usr.access_level = gitlab.const.AccessLevel.GUEST

			elif action == "enable":
				usr.access_level = gitlab.const.AccessLevel.DEVELOPER

			usr.save()

		elif self.server_choice == "gitea":

			url = f"/repos/{repo.owner.username}/{repo.name}/collaborators/{repo.name}"

			if action == "disable":
				#repo.edit_collaborator(usr, "read")
				self.server.requests_put(url, {"permission": "read"})

			elif action == "enable":
				#repo.edit_collaborator(usr, "write")
				self.server.requests_put(url, {"permission": "write"})



	def get_last_commit(self, project: Union[gitea.Repository, any]) -> Union[gitea.Commit, any]:
		commit = None
		if self.server_choice == "gitlab":
			commit = project.commits.list(ref_name='main')[0]
			#print(f"{project.name}\t{commit.created_at}\t{commit.committer_name}\t\t{commit.message}")

		elif self.server_choice == "gitea":
			commit = project.get_commits()[0]
			#print(f"{project.name}\t{commit.created}\t{commit.author.username}\t\t{commit.commit['message']}")

		return commit



	def parse_project(self, project: Union[gitea.Repository, any]) -> Union[gitea.Repository, any]:
		if self.server_choice == "gitlab":
			return self.server.projects.get(project.id)
		elif self.server_choice == "gitea":
			return project


	def create_hook(self, webhook_url: str, top_name: str, sub_names: tuple):
		if self.server_choice == "gitlab":
			self.hook = self.server.hooks.create({
											'url': webhook_url,
											'push_events': True
										})

		elif self.server_choice == "gitea":
			#org = self.get_group(top_name)
			#return org.org_create_hook(webhook_url)

			for sub_name in sub_names:
				for repo in self.get_projects(top_name, sub_name):
					repo.create_gitea_hook(webhook_url, ["push"])



	def delete_hook(self, top_name: str, sub_names: tuple):
		if self.server_choice == "gitlab":
			self.hook.delete()

		elif self.server_choice == "gitea":

			for sub_name in sub_names:
				for repo in self.get_projects(top_name, sub_name):

					hooks = repo.list_hooks()

					for hook in hooks:
						repo.delete_hook(hook['id'])





	def delete_user(self, user: Union[gitea.User,any]):
		if self.server_choice == "gitlab":
			self.server.users.delete(user.id)

		elif self.server_choice == "gitea":

			teams = user.get_teams()
			for team in teams:
				team.remove_team_member(user.username)

			user.delete()


	def delete_repo(self, project: Union[gitea.Repository, any]):
		if self.server_choice == "gitlab":
			project.delete()

		elif self.server_choice == "gitea":
			project.delete()


