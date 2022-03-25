import requests
import json
import os
import sys
from datetime import datetime

release = os.environ["RELEASE_TAG"]
if "CREATE_DATE" in os.environ:
    create_date = os.environ["CREATE_DATE"]
else:
    create_date = ""
failed_list = []


# function to get quay images using thr quay api call
def get_image():
    print(f"### Services : {services.strip()}")
    url = f"https://quay.io/api/v1/repository/cdis/{services}/tag/"
    print(url)
    res = requests.get(url)
    quay_result = json.loads(res.text)
    tags = quay_result["tags"]

    for tag in tags:
        if tag["name"] == release:
            print(f"{release} of {services} modified at {tag['last_modified']}")
            if create_date:
                # Format: 'Thu, 24 Mar 2022 16:12:50 -0000'
                last_modified_substring = tag["last_modified"][5:16]
                last_modified_date = datetime.strptime(
                    last_modified_substring, "%d %b %Y"
                )
                desired_date = datetime.strptime(create_date, "%d %b %Y")
                if not last_modified_date < desired_date:
                    print(f"{release} of {services} is up to date")
                    return
            else:
                print(f"{release} of {services} exists")
                return
    failed_list.append(services)
    print(f"{services} doesn't have up-to-date {release}")


# here
# key : github repo name
# value : quay image build name
repo_dict = {
    "pelican": "pelican-export",
    "docker-nginx": "nginx",
    "gen3-fuse": "gen3fuse-sidecar",
    "cloud-automation": "awshelper",
    "dataguids.org": "dataguids",
}

print("Check if the Quay Images are ready")
with open("repo_list.txt") as repoList:
    for repo in repoList:
        repo = repo.strip()
        services = repo
        if repo in repo_dict:
            services = repo_dict[repo]
            get_image()
            continue
        elif repo == "cdis-data-client":
            print(f"### Services : {services}")
            print("No docker image found")
            continue
        elif repo == "sower-jobs":
            print("Iterating through the list of images for sower-jobs")
            sower_jobs = [
                "metadata-manifest-ingestion",
                "get-dbgap-metadata",
                "manifest-indexing",
                "download-indexd-manifest",
            ]
            for sowerjob in sower_jobs:
                services = sowerjob.strip()
                get_image()
                continue
        elif repo == "ACCESS-backend":
            print("No docker image found")
            continue
        get_image()

print(f"List of repos that failed the check : {failed_list}")
# if the failed_list contains any repo name
# then the job should fail and print the list
if len(failed_list) > 0:
    sys.exit(1)
