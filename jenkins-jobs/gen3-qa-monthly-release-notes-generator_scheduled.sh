#!/bin/bash

# Runs on every 4th Friday of the month
# Schedule: 0 23 22-28 * 5
# e.g., Would last have run at Friday, February 26, 2021 11:00:29 PM UTC; would next run at Friday, March 26, 2021 11:00:29 PM UTC.

# Archive: *.md, *.json

pip3 install -U pip --user
pip3 install --editable git+https://github.com/uc-cdis/release-helper.git@gen3release#egg=gen3git --user

export PATH=$PATH:/home/jenkins/.local/bin:/home/jenkins/.local/lib

START_DATE=`date --date="41 day ago" +%Y-%m-%d`
END_DATE=`date --date="13 day ago" +%Y-%m-%d`
RELEASE_VERSION=`date --date="$END_DATE +1 month" +%Y.%m`
RELEASE_NAME="Core Gen3 Release $RELEASE_VERSION"

bash ./jenkins-jobs/generate_release_notes.sh $START_DATE $END_DATE $RELEASE_NAME

# The current logic does NOT handle the transition from December to January (tech debt)

YEAR=$(echo $RELEASE_VERSION | cut -d"." -f 1)
MONTH=$(echo $RELEASE_VERSION | cut -d"." -f 2)
CONVERTED_MONHT_STR_TO_NUMBER=$(expr $MONTH + 0)
#DECREMENTED_MONTH_NUM=$(( ${CONVERTED_MONHT_STR_TO_NUMBER} - 1 ))
#MONTHSTR=$(printf "%02d\n" $DECREMENTED_MONTH_NUM)

# Get the manifest from the previous month
curl "https://raw.githubusercontent.com/uc-cdis/cdis-manifest/master/releases/${YEAR}/${MONTHSTR}/manifest.json" -o manifest.json

# replace versions (TODO: Improve this logic to pick up new services from repos_list.txt)
sed -i "s/${YEAR}.${MONTHSTR}/${YEAR}.${MONTH}/" manifest.json

python3.8 -m pip install poetry --user
python3.8 -m pip install pygithub --user
python3.8 -m pip uninstall pygit2 --user
python3.8 -m pip uninstall gen3release -y

cd gen3release-sdk
python3.8 -m poetry build

wheel_file=$(ls dist | grep whl | tail -n1)

python3.8 -m pip install dist/${wheel_file} --user

cd $WORKSPACE

gen3release notes -v ${RELEASE_VERSION} -f gen3_release_notes.md ./manifest.json
