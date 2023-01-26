#!/bin/bash

# Runs on every 4th Friday of the month
# Schedule: 0 23 22-28 * 5
# e.g., Would last have run at Friday, February 26, 2021 11:00:29 PM UTC; would next run at Friday, March 26, 2021 11:00:29 PM UTC.

# Archive: *.md, *.json

pip3 install -U pip --user
pip3 install --editable git+https://github.com/uc-cdis/release-helper.git@gen3release#egg=gen3git --user

export PATH=$PATH:/home/jenkins/.local/bin:/home/jenkins/.local/lib

START_DATE="2022-12-10"
END_DATE="2023-01-17"
RELEASE_VERSION="2023.02"
RELEASE_NAME="Core Gen3 Release $RELEASE_VERSION"

echo "### Generating Release Notes ###"
bash ./jenkins-jobs/generate_release_notes.sh --startDate "$START_DATE" --endDate "$END_DATE" --releaseName "$RELEASE_NAME"

YEAR=$(echo $RELEASE_VERSION | cut -d"." -f 1)
MONTH=$(echo $RELEASE_VERSION | cut -d"." -f 2)
CURR_YEAR=$(date +%Y)
CURR_MONTH=$(date +%m)

# Get the manifest from the previous monthly release
curl "https://raw.githubusercontent.com/uc-cdis/cdis-manifest/master/releases/${CURR_YEAR}/${CURR_MONTH}/manifest.json" -o manifest.json

# replace versions (TODO: Improve this logic to pick up new services from repos_list.txt)
sed -i "s/${CURR_YEAR}.${CURR_MONTH}/${YEAR}.${MONTH}/" manifest.json

python3.8 -m pip install poetry --user
python3.8 -m pip install pygithub --user
python3.8 -m pip uninstall pygit2 --user
python3.8 -m pip uninstall gen3release -y

cd gen3release-sdk
python3.8 -m poetry build

wheel_file=$(ls dist | grep whl | tail -n1)

python3.8 -m pip install dist/${wheel_file} --user

cd $WORKSPACE

gen3release notes -v ${RELEASE_VERSION} -f gen3_release_notes.md manifest.json
