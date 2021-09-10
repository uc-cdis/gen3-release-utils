import requests
import json
import os

release = os.environ["RELEASE_TAG"]
failed_list = []


def get_image():
    print(f"### Services : {services.strip()}")
    url = f"https://quay.io/api/v1/repository/cdis/{services}/tag/{release}/images"
    print(url)
    res = requests.get(url)
    try:
        quay_result = json.loads(res.text)
        if len(quay_result["images"][0]) > 0:
            print("Created: ", quay_result["images"][0]["created"])
            print("ID: ", quay_result["images"][0]["id"])
            print(f"Image Exists for {services.strip()}")
    except KeyError:
        failed_list.append(services)
        print(f"The Image doesn't Exist for {services}")


print("Check if the Quay Images are ready")
with open("repo_list.txt") as repoList:
    for repo in repoList:
        repo = repo.strip()
        services = repo
        if repo == "pelican":
            services = "pelican-export"
            get_image()
            continue
        elif repo == "cdis-data-client":
            print(f"### Services : {services}")
            print("No docker image found")
            continue
        elif repo == "docker-nginx":
            services = "nginx"
            get_image()
            continue
        elif repo == "gen3-fuse":
            services = "gen3fuse-sidecar"
            get_image()
            continue
        elif repo == "cloud-automation":
            services = "awshelper"
            get_image()
            continue
        elif repo == "dataguids.org":
            services = "dataguids"
            get_image()
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
        elif repo == "mariner":
            print("Iterating though the list of images for mariner")
            mariner = ["mariner-engine", "mariner-s3sidecar", "mariner-server"]
            for marinerImage in mariner:
                services = marinerImage.strip()
                get_image()
        elif repo == "ACCESS-backend":
            print("No docker image found")
            continue
        get_image()

print(f"List of repos that failed the check : {failed_list}")
