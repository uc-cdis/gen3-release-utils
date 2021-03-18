#!/bin/bash +x

# String parameter FORK_FROM
#   Default value: master

# Every 2nd Friday of every month
# Schedule: 0 21 8-15 * 5
# e.g, Would last have run at Friday, March 12, 2021 9:00:26 PM UTC; would next run at Friday, April 9, 2021 9:00:26 PM UTC.

# Obtained through Jenkins credentials
# GITHUB_USERNAME
# GITHUB_TOKEN

latest_release=$(git ls-remote --tags https://github.com/uc-cdis/fence | grep "/202" | grep -v "\^{}" | awk '{ print $2 }' | cut -d "/" -f3 | tail -n1)

BRANCH_NAME=""
if [[ $latest_release =~ [0-9]{4}\.([0-9]{2}) ]]; then
  echo "match"
  CONVERTED_MONTH_STR_TO_NUMBER=$(expr ${BASH_REMATCH[1]} + 0)
  INCREMENTED_MONTH_NUM=$(( ( ($CONVERTED_MONTH_STR_TO_NUMBER) + 1 ) % 12 ));
  BRANCH_NAME=$(printf "%02d\n" $INCREMENTED_MONTH_NUM)
  echo "creating branch integration2021${BRANCH_NAME}..."
  ./make_branch.sh "$FORK_FROM" "integration2021${BRANCH_NAME}"
else
  echo "not match. Skip branch creation."
fi
