import requests
import yaml
from github import Github


def read_config():
    with open("config.yaml", 'r') as stream:
        try:
            parsed_yaml = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    return parsed_yaml


def mirror(url: str, headers: dict, payload: dict, enable_ssl: bool = True) -> None:
    requests.post(url=url, headers=headers, json=payload, verify=enable_ssl)


def get_headers(token: str) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"token {token}",
    }
    return headers


def get_payload(token: str, org: str, repo: str, owner: str, private: bool = True) -> dict:
    payload = {
        "service": "github",
        "auth_token": token,
        "clone_addr": f"https://github.com/{org}/{repo}",
        "mirror": True,
        "private": private,
        "repo_name": repo,
        "repo_owner": owner,
    }
    return payload


def get_repos(token: str, org: str) -> dict:
    g = Github(token)
    organization = g.get_organization(org)
    repos = organization.get_repos(type="all")
    return repos


def mirror_org(
    github_pat: str,
    github_org: str,
    gitea_owner: str,
    gitea_token: str,
    gitea_api_url: str,
    gitea_api_ssl: bool = True,
) -> None:

    for repo in get_repos(token=github_pat, org=github_org):
        mirror(
            url=f"{gitea_api_url}/repos/migrate",
            headers=get_headers(gitea_token),
            payload=get_payload(
                token=github_pat,
                org=github_org,
                repo=repo.name,
                private=repo.private,
                owner=gitea_owner,
            ),
            enable_ssl=gitea_api_ssl
        )


config = read_config()
mirror_org(
    github_pat=config['github_pat'],
    github_org=config['github_org'],
    gitea_api_url=config['gitea_api_url'],
    gitea_api_ssl=config['gitea_api_ssl'],
    gitea_token=config['gitea_token'],
    gitea_owner=config['gitea_owner'],
)

