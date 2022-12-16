# python-gitlab.cfg

```
[global]
default = local

[local]
url = https://172.16.73.132
private_token = <TOKEN>
```

To create a token, go to "User Settings" by clicking on "Preferences" under user icon, then go to "Access Tokens", then create a new token with all scopes enabled.

Shortcut: (https://172.16.73.132/-/profile/personal_access_tokens)


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
