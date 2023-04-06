import csv

from datetime import datetime, timedelta
from github import Github


# Startdatum abfragen
since = str(datetime.date(datetime.now() - timedelta(days=7)))
since = input(f"Start [{since}]: ") or since
since = datetime.strptime(since, '%Y-%m-%d')

# Enddatum abfragen
until = str(datetime.date(since + timedelta(days=7)))
until = input(f"Ende [{until}]: ") or until
until = datetime.strptime(until, '%Y-%m-%d')

# Github Daten abfragen
org = input("Github organization [osism]: ") or "osism"
user = input("Github username [tibeer]: ") or "tibeer"
token = input("Github token: ")
gh_handle = Github(login_or_token=token)
org_handle = gh_handle.get_organization(org)
user_handle = gh_handle.get_user(user)

# Alle Repos, Branches und Commits durchsuchen
lines = []
for repo in org_handle.get_repos():
    print(f"Working on {repo.full_name}")
    for branch in repo.get_branches():
        for commit in repo.get_commits(
                sha=branch.name,
                since=since,
                until=until,
                author=user_handle
        ):
            # Passende Commits merken
            lines.append(
                [
                    commit.commit.author.date,
                    repo.full_name,
                    branch.name,
                    commit.commit.message,
                    ""
                ]
            )

# Commits in eine CSV ausgeben
with open(f"{str(datetime.date(since))}_{str(datetime.date(until))}.csv", 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile, dialect=csv.unix_dialect, delimiter=';')
    # Print headline
    csvwriter.writerow(["Datum", "Repo", "Branch", "Commit", "Hours"])
    for line in lines:
        csvwriter.writerow(line)
