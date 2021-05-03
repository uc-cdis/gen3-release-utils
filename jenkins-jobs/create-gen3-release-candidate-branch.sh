#!/bin/bash

# String parameter FORK_FROM
#   Default value: master
# String parameter RELEASE_VERSION
#   Default value: 2021.06

export GITHUB_USERNAME="themarcelor"
# GITHUB_TOKEN obtained from Jenkins Credentials


BRANCH_NAME=""
if [[ $RELEASE_VERSION =~ [0-9]{4}\.([0-9]{2}) ]]; then
  echo "match"
  CONVERTED_MONHT_STR_TO_NUMBER=$(expr ${BASH_REMATCH[1]} + 0)
  BRANCH_NAME=$(printf "%02d\n" $CONVERTED_MONHT_STR_TO_NUMBER)
  echo "creating branch integration2021${BRANCH_NAME}..."
  ./make_branch.sh "$FORK_FROM" "integration2021${BRANCH_NAME}"
else
  echo "not match. Skip branch creation."
fi
