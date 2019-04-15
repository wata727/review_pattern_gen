"""
Usage: python3 collect_pulls.py
"""
import sys
from csv import DictWriter
from time import sleep
from github import Github
import configparser

config = configparser.ConfigParser()
config.read('config')
user = config["GitHub"]["id"]
password = config["GitHub"]["password"]
owner = config["Target"]["owner"]
repo = config["Target"]["repo"]
lang = config["Target"]["lang"]

g = Github(user, password)
sha_fields = [
    "number",
    "commit_len",
    "base_commit_sha",
    "head_commit_sha",
    "merge_commit_sha",
    "created_at",
    "merged_at",
    "merged_by",
    "1-n_url"
]


def get_pulls(owner, repo_name):
    results = []
    print(owner + "/" + repo_name)
    repo = g.get_repo(owner + "/" + repo_name)
    pulls = repo.get_pulls(state='close', sort='created', base='master')

    for x in pulls:
        if not x.merged:
            continue
        sys.stdout.write("\rProcessing PR number: %d" % (x.number))
        ratelimit = g.get_rate_limit().core.remaining
        if ratelimit < 100:
            print("Sleeping for replenish rate limit")
            sleep(3600)
            ratelimit = g.get_rate_limit().core.remaining
        results.append({
            "number": x.number,
            "commit_len": x.commits,
            "base_commit_sha": x.base.sha,
            "head_commit_sha": x.head.sha,
            "merge_commit_sha": x.merge_commit_sha,
            "1-n_url": x.diff_url,
            "created_at": x.created_at,
            "merged_at": x.merged_at,
            "merged_by": x.merged_by.login
        })
    return results


def out_pulls(path, results):
    with open(path, "w", encoding="utf-8") as commits:
        writer = DictWriter(commits, sha_fields)
        writer.writeheader()
        writer.writerows(results)


def main():
    results = get_pulls(owner, repo)
    out_pulls("data/pulls/" + owner + "_" + repo + ".csv", results)

if __name__ == '__main__':
    main()
