import requests
from requests.auth import HTTPBasicAuth
import json
import os
import re
import logging
from datetime import datetime, timedelta

gh_user = os.environ["GITHUB_USERNAME"]
gh_token = os.environ["GITHUB_TOKEN"]

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
log = logging.getLogger(__name__)

log.info(
    f"Shooting a GET request to https://api.github.com/repos/uc-cdis/cdis-manifest/pulls?state=open..."
)
get_pull_requests = requests.get(
    # f"https://api.github.com/repos/uc-cdis/cdis-manifest/pulls?state=open",
    f"https://api.github.com/repos/uc-cdis/cdis-manifest/pulls",
    auth=(gh_user, gh_token),
)

for pr in get_pull_requests.json():
    if "Nightly Build" in pr["title"]:
        log.info(f"pr number#: {pr['number']}")
        log.info(f"pr title#: {pr['title']}")
        log.info(f"pr created_at#: {pr['created_at']}")

        # checking if the nightly build PR is older than 1 week
        today = datetime.now()
        # sample github timestamp: created_at#: 2021-07-22T04:38:33Z
        pr_created_at = datetime.strptime(pr["created_at"], "%Y-%m-%dT%H:%M:%SZ")

        log.debug(f"today #: {today}")
        log.debug(f"pr_created_at #: {pr_created_at}")

        if pr_created_at < today - timedelta(days=7):
            log.info(
                f"pr {pr['title']} is eligible for closing. created_at#: {pr['created_at']}"
            )
        else:
            log.info(f"Skipping PR {pr['title']}...")

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
