# python-gitlab.cfg

```
[global]
default = local

[local]
url = https://172.16.73.132
private_token = <TOKEN>
```

# Generate users and repositories

```
$ python3 create_repo.py -i ~/Downloads/studenti.xlsx  --subgroup test-1 --repo testrepo/ --ref testrepo/reference/
```

# Enable/disable user permissions

```
$ python3 enable_users.py --disable --subgroup test-1
$ python3 enable_users.py --enable --subgroup test-1
```

# Delete users

```
$ python3 remove_users.py -i ~/Downloads/studenti.xlsx
```

# Generate sheet with credentials

```
$ generate_sheet.py -i ~/Downloads/studenti.xlsx -t template/template.docx  -o generated_sheet.docx
```

Groups can be deleted from GitLab dashboard (https://172.16.73.132/admin/groups)
