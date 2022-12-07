from datetime import datetime
import requests
from requests.auth import HTTPBasicAuth
import os
import re
import logging
from datetime import datetime, timedelta

DELETE_AFTER_DAYS = 7  # how many days to keep nightly build PRs and branches

gh_user = os.environ["GITHUB_USERNAME"]
gh_token = os.environ["GITHUB_TOKEN"]

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
log = logging.getLogger("close-nightly-prs")

today = datetime.now()
log.debug(f"today: {today}")

# only get the first 100 PRs. the latest nightly build PRs should be there
url = "https://api.github.com/repos/uc-cdis/cdis-manifest/pulls?state=open&per_page=100"
log.info("Shooting a GET request to {url}...")
resp = requests.get(url, auth=(gh_user, gh_token))
resp.raise_for_status()
pull_requests = resp.json()

for pr in pull_requests:
    if "Nightly Build" in pr["title"]:
        log.info(f"pr number#: {pr['number']}")
        log.info(f"pr title#: {pr['title']}")
        log.info(f"pr created_at#: {pr['created_at']}")

        # checking if the nightly build PR is older than 1 week
        # sample github timestamp: created_at#: 2021-07-22T04:38:33Z
        pr_created_at = datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ")

        if pr_created_at < today - timedelta(days=DELETE_AFTER_DAYS):
            log.info(
                f"pr {pr['title']} is eligible for closing. created_at#: {pr['created_at']}"
            )
            try:
                url = f"https://api.github.com/repos/uc-cdis/cdis-manifest/pulls/{pr['number']}"
                res = requests.patch(
                    url, json={"state": "closed"}, auth=HTTPBasicAuth(gh_user, gh_token)
                )
                res.raise_for_status()
            except requests.exceptions.HTTPError as httperr:
                log.error(
                    "request to {0} failed due to the following error: {1}".format(
                        url, str(httperr)
                    )
                )
                os.exit(1)
            print(f"the PR {pr['title']} is now closed.")
        else:
            log.info(f"Skipping PR {pr['title']}...")

# only get the first 100 branches. the latest nightly build branches should be there
url = "https://api.github.com/repos/uc-cdis/cdis-manifest/branches?per_page=100"
log.info(f"Shooting a GET request to {url}...")
resp = requests.get(url, auth=(gh_user, gh_token))
resp.raise_for_status()
branches = resp.json()

for branch in branches:
    branch_name = branch["name"]
    if "Nightly(" not in branch_name:
        continue

    nightly_build_date = re.search("^Nightly\((\d{2}-\d{2}-\d{4})\)$", branch_name)
    if not nightly_build_date:
        log.info(f"Could not parse date out of branch name '{branch_name}': skipping.")
        continue

    # checking if the nightly build branch is older than 1 week
    created_at = datetime.strptime(nightly_build_date.group(1), "%m-%d-%Y")
    if created_at < today - timedelta(days=DELETE_AFTER_DAYS):
        log.info(f"Branch {branch_name} is eligible for deleting.")
        try:
            url = f"https://api.github.com/repos/uc-cdis/cdis-manifest/git/refs/heads/{branch_name}"
            res = requests.delete(
                url, json={"state": "closed"}, auth=HTTPBasicAuth(gh_user, gh_token)
            )
            res.raise_for_status()
        except requests.exceptions.HTTPError as httperr:
            log.error(
                "request to {0} failed due to the following error: {1}".format(
                    url, str(httperr)
                )
            )
            os.exit(1)
        print(f"the branch {branch_name} is now closed.")
    else:
        log.info(f"Skipping branch {branch_name}...")
