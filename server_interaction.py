import os
import shutil
import gitlab
from git import Repo
from gitea import *
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
			
			self.server_url=urlparse(config.url).netloc
			
		
		elif server_choice == "gitea":
		
			self.server = Gitea(gitea_url = "http://localhost:3000",
				token_text="fdc94f06ad1d4c9989b432679dbb7421b5528d93")
			self.server_url=urlparse("http://127.0.0.1").netloc
		
		self.server_choice = server_choice
			
			
	def get_url(self):
		return self.server_url
	
	
	def get_clone_url(self, project: Union[Repository, any]) -> str:
		
		if self.server_choice == "gitlab":
			return f"{self.server_url}/{project.path_with_namespace}"	
		
		elif self.server_choice == "gitea":
			return project.clone_url.replace("http://","")
		
	def get_users(self) -> list[Union[User, any]]:
	
		if self.server_choice == "gitlab":
			return self.server.users.list(get_all=True)
			
		elif self.server_choice == "gitea":
			return self.server.get_users()
	
	
	
	def get_user(self, username: str) -> Union[User,any]:
		
		if self.server_choice == "gitlab":
			return self.server.users.list(username = username)[0]
		
		elif self.server_choice == "gitea":
			return User.request(self.server, username)
	
	
	
	def get_group(self, group_name: str) -> Union[Organization, any]:
	
		if self.server_choice == "gitlab":
			return self.server.groups.list(search=group_name)[0]
			
		elif self.server_choice == "gitea":
			return Organization.request(self.server, group_name)
			
		
			
	def get_subgroup(self, top_group:Union[Organization,any], sub_name: str) -> Union[Team, any]:
	
		if self.server_choice == "gitlab":
			return top_group.subgroups.list(search=sub_name)[0]
		
		elif self.server_choice == "gitea":
			return top_group.get_team(sub_name)
			
			
	
	def create_group(self, group_name: str) -> Union[Organization, any]:
	
		if self.server_choice == "gitlab":
			return self.server.groups.create({'name': group_name, 'path': group_name})
			
		elif self.server_choice == "gitea":
			owner = User.request(self.server, "gaetanocelentano") # query to get the server owner
			self.server.create_org(owner, group_name)
			return Organization.request(self.server, group_name)
		
		
			
	def create_subgroup(self, group: Union[Organization, any], sub_name: str) -> Union[Team, any]:
		
		if self.server_choice =="gitlab":
			return self.create_group(self.server_choice, sub_name)
		
		elif self.server_choice == "gitea":
			self.server.create_team(group, sub_name)
			return self.get_subgroup(group, sub_name)
		
		
			
	def create_user(self, usr_info: list) -> Union[User, any]:
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
			return User.request(self.server, usr_info[0])
	
	
	
	def create_project(self, project_name: str, group: Union[Organization, any], subgroup_name: str) -> Union[Repository, any]:
		subgroup = self.get_subgroup(group, subgroup_name)
		if self.server_choice == "gitlab":
			return self.server.projects.create(
		                    {'name': project_name,
		                    'default_branch': 'main',
		                    'initialize_with_readme': 'true',
		                    'namespace_id': subgroup.id
		                    })
		                    
		elif self.server_choice == "gitea":
			group.create_repo(repoName = project_name) # default_branch and readme inizialization are by default in the used module
			
			project = Repository.request(self.server, owner = group.name, name = project_name)
			
			subgroup.add_repo(group, project)
			
			return project 
	
	
	
	def get_project(self, group: Union[Organization, any], project_name: str) -> Union[Repository, any]:
		
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
			group = Organization.request(self.server, top_name)
			subgroup = group.get_team(sub_name)
			return subgroup.get_repos()
	
	
	
	def add_member(self,group: Union[Organization, any],  project_name: str, username: str):
		
		user = self.get_user(username)
		project = self.get_project(group, project_name)
		if self.server_choice == "gitlab":
			member = project.members.create({'user_id': user.id, 'access_level':
		                                    gitlab.const.AccessLevel.DEVELOPER})
		                                    
		elif self.server_choice == "gitea":
			project.add_collaborator(user)
			
	
	def protect_main_branch(self,group: Union[Organization,any], project_name: str, whitelist_usr:str):
		
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
			project.add_branch_protections(data = {"branch_name":"master",
		    										"enable_push":True,
		    										"enable_merge_whitelist":True,
		    										"merge_whitelist_usernames": [whitelist_usr]
		    										})
		
			
	def get_member(self, project: Union[Repository, any]) -> Union[User, any] :
		
		if self.server_choice == "gitlab":
			project = self.projects.get(project.id)
			return project.members.list(query=project.name)[0]
			
		elif self.server_choice == "gitea":
			server_owner = User.request(self.server, "gaetanocelentano") # server owner
			users = project.get_users_with_access()
			users.remove(server_owner)
			for usr in users:
				return usr #doing this because for some reason users[0] is "out of range"
	
	
	
	def edit_member_access(self, usr : Union[User, any], action: str, repo: Repository) -> None:
		
		if self.server_choice == "gitlab":
			if action == "disable":
				usr.access_level = gitlab.const.AccessLevel.GUEST
			
			elif action == "enable":
				usr.access_level = gitlab.const.AccessLevel.DEVELOPER
			
			member.save()
		
		elif self.server_choice == "gitea":
			if action == "disable":
				repo.edit_collaborator(usr, "read")
			
			elif action == "enable":
				repo.edit_collaborator(usr, "write")
		
		
			
	def get_last_commit(self, project: Union[Repository, any]) -> Union[Commit, any]:
		commit = None
		if self.server_choice == "gitlab":
			commit = project.commits.list(ref_name='main')[0]
			print(f"{project.name}\t{commit.created_at}\t{commit.committer_name}\t\t{commit.message}")
		
		elif self.server_choice == "gitea":
			commit = project.get_commits()[0]
			print(f"{project.name}\t{commit.created}\t{commit.author.username}\t\t{commit.commit['message']}")
			
		return commit
		                        
	
	
	def parse_project(self, project: Union[Repository, any]) -> Union[Repository, any]:
		if self.server_choice == "gitlab":
			return self.server.projects.get(project.id)
		elif self.server_choice == "gitea":
			return project
	
	
	def create_hook(self, webhook_url: str, top_name: str) -> any:
		if self.server_choice == "gitlab":
			return self.server.hooks.create({
											'url': webhook_url,
											'push_events': True
										})
	
		elif self.server_choice == "gitea":
			org = self.get_group(top_name)
			return org.create_org_hook(webhook_url)
	
	
			
	def delete_hook(self, top_name:str):
		group = Organization.request(self.server, top_name)
		group.delete_org_hook()
			
	
	
	def delete_user(self, user: Union[User,any]):
		if self.server_choice == "gitlab":
			self.server.users.delete(user.id)
			
		elif self.server_choice == "gitea":
			self.server.delete_usr(user)

		
