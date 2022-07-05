#!/bin/bash

# String parameter REPO_NAME
#   Example: data-portal
# String parameter COMMIT_ID
#   Example: 4fd40e7bcf9aca7d0f5613a23c377f20eb32512a
# String parameter RELEASE_VERSION
#   Example: 2021.06

# GITHUB_USERNAME obtained from Jenkins Credentials
# GITHUB_TOKEN obtained from Jenkins Credentials

# clone the repo
git clone https://github.com/uc-cdis/${REPO_NAME}.git
# check out stable
git checkout stable
git pull
# cherry-pick commit
git cherry-pick -m 1 ${COMMIT_ID}
# print git log top 5 lines
git log | cat | head -n5
# delete existing tag
git tag -d ${RELEASE_VERSION}
git push origin --delete ${RELEASE_VERSION}
# push new tag
git tag ${RELEASE_VERSION} -a -m "Gen3 Core Release ${RELEASE_VERSION}"
git push origin --tags
