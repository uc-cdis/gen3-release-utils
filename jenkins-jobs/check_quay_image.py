import requests
import json
import os

release = os.environ["Release_Tag"]


def get_image():
    print(f"### Services : {services.strip()}")
    url = "https://quay.io/api/v1/repository/cdis/{}/tag/2021.09/images".format(
        services.strip()
    )
    print(url)
    res = requests.get(url)
    quay_result = json.loads(res.text)
    if len(quay_result["images"][0]) > 0:
        print("Created: ", quay_result["images"][0]["created"])
        print("ID: ", quay_result["images"][0]["id"])
        print("Image Exists")


print("Check if the Quay Images are ready")
with open("../repo_list.txt") as repoList:
    for repo in repoList:
        services = repo
        if repo.strip() == "pelican":
            services = "pelican-export"
            get_image()
            continue
        elif repo.strip() == "cdis-data-client":
            print(f"### Services : {services.strip()}")
            print("No docker image found")
            continue
        elif repo.strip() == "docker-nginx":
            services = "nginx"
            get_image()
            continue
        elif repo.strip() == "gen3-fuse":
            services = "gen3fuse-sidecar"
            get_image()
            continue
        elif repo.strip() == "cloud-automation":
            services = "awshelper"
            get_image()
            continue
        elif repo.strip() == "dataguids.org":
            services = "dataguids"
            get_image()
            continue
        elif repo.strip() == "sower-jobs":
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
        elif repo.strip() == "mariner":
            print("Iterating though the list of images for mariner")
            mariner = ["mariner-engine", "mariner-s3sidecar", "mariner-server"]
            for image in mariner:
                services = image.strip()
                get_image()
        elif repo.strip() == "ACCESS-backend":
            print("No docker image found")
            continue
    get_image()
