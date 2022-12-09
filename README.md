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

Groups can be delete from (https://172.16.73.132/admin/groups)
