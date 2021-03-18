#!/bin/bash

# String parameter FORK_FROM
#   Default value: master

export GITHUB_USERNAME="themarcelor"
# GITHUB_TOKEN obtained from Jenkins Credentials

latest_release=$(git ls-remote --tags https://github.com/uc-cdis/fence | grep "/202" | grep -v "\^{}" | awk '{ print $2 }' | cut -d "/" -f3 | tail -n1)

BRANCH_NAME=""
if [[ $latest_release =~ [0-9]{4}\.([0-9]{2}) ]]; then
  echo "match"
  CONVERTED_MONHT_STR_TO_NUMBER=$(expr ${BASH_REMATCH[1]} + 0)
  INCREMENTED_MONTH_NUM=$(( ( ($CONVERTED_MONTH_STR_TO_NUMBER) + 1 ) % 12 ));
  BRANCH_NAME=$(printf "%02d\n" $INCREMENTED_MONTH_NUM)
  echo "creating branch integration2021${BRANCH_NAME}..."
  ./make_branch.sh "$FORK_FROM" "integration2021${BRANCH_NAME}"
else
  echo "not match. Skip branch creation."
fi
