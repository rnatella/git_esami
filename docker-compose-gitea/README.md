# Docker-Compose-Gitea

A Docker Compose file for Gitea - Git with a cup of tea ([gitea.io](https://gitea.io))

Data will be saved in separate docker volumes to enable easy upgrades!

## Requirements

* docker
* docker-compose

## Getting Started

1. Copy [.env.dist](.env.dist) to **.env** and make your modifications
2. See [HTTPS setup to encrypt connections to Gitea](https://docs.gitea.io/en-us/https-setup/) to set up HTTPS support if needed or desired.
   * **Note:** If the built-in HTTPS server is to be used it is best to manually edit the app.ini inside the docker container once the server is running.
3. Start docker containers:
```bash
$ docker-compose up -d
```

After that open gitea installer via browser: [http://localhost:3000](http://localhost:3000) and fill the form according your .env settings. 

Set **`db:3306`** in _Host_ field and complete setup.

After setup is completed register a new user (use link from the navigation bar).

The first registered user has admin privileges.


### Environment Configuration

| VARIABLE            | Description                          | DEFAULT       |
| --------------------|--------------------------------------|:-------------:|               
|GITEA_VERSION        | Docker-Image-Version                 |latest         |
|GITEA_HOSTNAME       | Hostname for Gitea Application       |localhost      |
|GITEA_WEB_PORT       | GUI-Port for accessing Gitea         |3000           |
|GITEA_SSH_PORT       | Port for accessing Gitea via SSH     |2222           |
|MYSQL_ROOT_PASSWORD  | MySQL root password                  |root           |
|MYSQL_DATABASE       | Database name for gitea              |gitea          |
|MYSQL_USER           | Database user for gitea              |gitea          |
|MYSQL_PASSWORD       | Password for MySQL user              |gitea          |
|USER_UID             | User ID to run the gitea container   |1000           |
|USER_GID             | Group ID to run the gitea container  |1000           |

## Create systemd unit
1. Copy **docker-gitea.service.dist** to **docker-gitea.service**
1. Adjust **WorkingDirectory** in service file if needed
1. Create symbolic link: ``ln -s docker-gitea.service /etc/systemd/system/docker-gitea.service``
1. Start service: ``systemctl start docker-gitea``
1. (optional) Enable autostart at boot: ``systemctl enable docker-gitea``
