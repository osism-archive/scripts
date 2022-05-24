# Gitea mirror script

This script mirrors all repositories of a github organization to a gitea installation while keeping almost everything (privacy status, labels, descriptions, etc.)

## How to use

Execute the following command in the directory where the `config.yaml` file is stored.

```sh
python3 mirror.py
```

## How to configure

Alter the `config.yaml`:

```yaml
gitea_token: # A token you created for your user
gitea_owner: # the desired owner of the mirrored repositories
gitea_api_url: # API URL of Gitea
gitea_api_ssl: # False or True. Use SSL or not to connect to gitea. Used for testing mainly.
github_pat: # Personal Access Token with complete repository access. Watch out! This should not expire, otherwise your mirrors won't update once expired.
github_org: # Name of the github organization you want to mirror
```

