# PMGC (Poor Man's Git Classroom)

This project is a collection of scripts and configurations to handle programming assignments, using a Git management platform (Gitea or Gitlab).

![Overview](/images/overview.png)


The student opens a web form, and inserts his/her data (surname, name, ID number). The student can also select a group: for example, groups can be used to handle students from different classrooms, or to distribute different assignments.

![Demo form](/images/demo-form.png)


After submitting the form, in the response page the student receives a dedicated account (e.g., student-10, with random password) to access the Git server. Every account has a dedicated Git repository, with the same name of the username (e.g., student-10).

The student will also find Git commands to:
- clone the dedicated repository on his/her local computer, and configure the repo
- push changes to the server

![Demo git](/images/demo-git.png)


The web page with the account data and commands can be safely reloaded. The session on the web form lasts for 2 hours by default. Thus, the student can reload the browser or reboot the computer. The server can also be safely rebooted without losing the sessions. The server saves session tokens on the filesystem, in the folder `flask_session`. The encryption key is generated randomly at the first execution of the web form, and saved in `.flaskenv`.


The teacher can monitor in real-time the commits pushed by students, using a console UI.

![Overview](/images/demo-console.png)

Before distributing the assignments, the teacher has to create the student accounts. It suffices to indicate which groups to create, and how many accounts to create per group. It is not required (although it is possible) to insert student data in the accounts (name, surname, etc.), since they will insert their personal information through the web form.


The project provides the following scripts to manage accounts and repositories:
- **docker-compose-gitea/gitea_configure.sh**: Runs containers for Gitea and MySQL.
- **docker-compose-gitea/gitea_token.sh**: Gets a token to access Gitea through REST API (saved in **gitea.toml**).
- **docker-compose-gitea/gitea_https.sh**: Enables HTTPS in Gitea (with a self-signed certificate).
- **exams_create.sh**: Creates accounts both on Gitea (stored in MySQL) and on the web form (save in a SQLite db **students.db**).
- **exams_web_form.sh**: Runs a Flask app that provides a web form for students for initial access.
- **exams_disable.sh**: Disables commit pushes (for all groups, or for a specific group).
- **exams_enable.sh**: Enbles commit pushes (for all groups, or for a specific group).
- **exams_list.sh**: Lists groups.
- **exams_monitor.sh**: Shows pushed commits from students in real-time.
- **exams_pull_repos.sh**: Clones/pulls the repositories for all students.
- **exams_delete.sh**: Removes everything (containers, DBs, repositories, etc.)


# Quick tutorial

Configure Python environment

```
$ python3 -m venv env
$ source env/bin/activate
$ pip install -r requirements.txt
```


Deploy local Gitea+DB server

```
cd docker-compose-gitea/

./gitea_configure.sh
...enter admin password...
...you can leave "0.0.0.0" (default) as server address...
...you can leave 3000 (default) as port...

./gitea_token.sh

./gitea_https.sh

cd ..
```



Initialize accounts for users (e.g., 2 groups, different code per group, 10 students per group, 20 students in total)
```
./exams_create.sh  so-sangiovanni  10  ./1st-folder-with-code
./exams_create.sh  so-fuorigrotta  20  ./2nd-folder-with-code
```

In a new shell, launch the web form. You can configure here the public IP address of the Git server, by setting the environment variable `GIT_SERVER_IP`. The students will receive a GIT URL with this IP address. You can set `FLASK_USE_HTTPS` to enable HTTPS with a self-signed certificate.
```
source env/bin/activate
export GIT_SERVER_IP="1.2.3.4"
export FLASK_USE_HTTPS=1
export FLASK_RUN_PORT=8000
./exams_web_form.sh
```

In a new shell, get updates in real-time about commits from students
```
source env/bin/activate
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


# Tutorial for dockerized scripts

Deploy Gitea as before (use `gitea_configure.sh`, `gitea_token.sh`, `gitea_https.sh`).

Build the container image for the scripts:
```
docker build -t git_esami -f docker/Dockerfile .
```

Create and manage exams with the following commands:
```
# To initialize users (can be ran multiple times)
./docker/exams_create.sh so-test 10 ./path-to-source

# From a dedicated shell
export GIT_SERVER_IP="1.2.3.4"
export FLASK_USE_HTTPS=1
export FLASK_RUN_PORT=8000
./docker/exams_web_form.sh

# From a dedicated shell
./docker/exams_monitor.sh

# From a dedicated shell
./docker/exams_disable.sh
./docker/exams_enable.sh
./docker/exams_pull_repos.sh

```
