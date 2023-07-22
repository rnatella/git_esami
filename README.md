# Setup

```
$ python3 -m venv env
$ source env/bin/activate
$ pip install -r requirements.txt
```

# Quick tutorial

Deploy local Gitea+MariaDB server

```
cd docker-compose-gitea/

./gitea_configure.sh
...enter admin password...
...enter public IP address...

./gitea_token.sh

cd ..
```

Initialize accounts for users
```
./exams_create.sh  esame-2023-07  10  ./folder-with-code
```

In a new shell, launch web form for students (e.g., http://172.16.73.132:5000)
```
export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=5000
flask  --app web_form_app run
```

In a new shell, get updates about commits from students
```
./exams_monitor.sh
```

To turn off submissions
```
./exams_disable.sh
```

To download all repositories
```
./exams_pull_repos.sh
```


To delete everything (DB, flask sessions, code repos)
```
./exams_delete.sh
```


# Configuration files

To use these scripts with GitLab, edit `python-gitlab.cfg`:
```
[global]
default = local

[local]
url = https://172.16.73.132
private_token = <TOKEN>
```

To create a token, go to "User Settings" by clicking on "Preferences" under user icon, then go to "Access Tokens", then create a new token with all scopes enabled.

Shortcut: (https://172.16.73.132/-/profile/personal_access_tokens)

To use these scripts with Gitea, edit `gitea.toml`:
```
[global]
default = "local"

[local]
url = 'http://127.0.0.1:3000'
token = '<TOKEN>'
```

To use webhooks, you need to add in `conf/app.ini`:
```
[webhook]
ALLOWED_HOST_LIST = *
```

# Generate users and repositories

```
$ python3 create_repo.py -i ~/Downloads/studenti.xlsx  --subgroup mysubgroup --repo ./testrepo/ --ref ./testrepo/reference/
```


# Enable/disable user permissions

```
$ python3 enable_users.py --disable --subgroup mysubgroup
$ python3 enable_users.py --enable --subgroup mysubgroup
```


# Check/pull last commit

Get info about HEAD commit in each repository, **by group/subgroup**:
```
$ python3 check_repo.py -i ~/Downloads/studenti.xlsx -s mysubgroup
```

Get info about HEAD commit in each repository, **from XLSX list**:
```
$ python3 check_repo.py -i ~/Downloads/studenti.xlsx
```

Get info about HEAD commit for a **specific user**:
```
$ python3 check_repo.py -u student-123
```

**Pull** HEAD commit on local repository:
```
$ python3 check_repo.py -s mysubgroup  --pull -r ./testrepo/
```


# Delete users

```
$ python3 remove_users.py -i ~/Downloads/studenti.xlsx
```


# Delete groups

Groups can be deleted from GitLab dashboard.

Shortcut: (https://172.16.73.132/admin/groups)


# Generate sheet with credentials

Generate sheet from multiple XLSX files, by **replacing domain** within Git repository URL:
```
$ python3 generate_sheet.py -i ~/Downloads/gruppo*.xlsx -t template/template.docx  -o generated_sheet.docx  --replace_domain 192.168.2.1
```


# Web user interface (students get username/password)

```
export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=5000
flask  --app web_form_app run
```

