#!/bin/bash

# String parameter RELEASE_VERSION
#   e.g., 2020.08

# String parameter RELEASE_NAME
#   e.g., Core Gen3 Release 202008 (Gold Coast)

# String parameter START_DATE
#   e.g., 2020-06-12

# String parameter END_DATE
#   e.g., 2020-07-10

# GITHUB_USERNAME
# GITHUB_TOKEN
# Obtained through Jenkins credentials

pip install --editable git+https://github.com/uc-cdis/release-helper.git@gen3release#egg=gen3git --user

export PATH=$PATH:/home/jenkins/.local/bin:/home/jenkins/.local/lib

./generate_release_notes.sh

YEAR="2021"
MONTH=$(echo $RELEASE_VERSION | cut -d"." -f 2)
CONVERTED_MONHT_STR_TO_NUMBER=$(expr $MONTH + 0)
DECREMENTED_MONTH_NUM=$(( ${CONVERTED_MONHT_STR_TO_NUMBER} - 1 ))
MONTHSTR=$(printf "%02d\n" $DECREMENTED_MONTH_NUM)

# Get the manifest from the previous month
curl "https://raw.githubusercontent.com/uc-cdis/cdis-manifest/master/releases/${YEAR}/${MONTHSTR}/manifest.json" -o manifest.json

# replace versions (TODO: Improve this logic to pick up new services from repos_list.txt)
sed -i "s/${YEAR}.${MONTHSTR}/${YEAR}.${MONTH}/" manifest.json

python3.6 -m pip install poetry --user
python3.6 -m pip install pygithub --user

python3.6 -m pip uninstall gen3release -y

cd gen3release-sdk
python3.6 -m poetry build

wheel_file=$(ls dist | grep whl | tail -n1)

python3.6 -m pip install dist/${wheel_file} --user

cd $WORKSPACE

# Commenting this out as we need to figure out the decrement logic first
# gen3release notes -v ${RELEASE_VERSION} -f gen3_release_notes.md manifest.json
