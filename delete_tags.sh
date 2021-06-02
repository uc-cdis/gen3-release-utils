#!/bin/bash

# this script serves the purpose only when the release process is messed up
# so before you run/ execute this script please ask for a peer review

urlPrefix="https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/uc-cdis/"
tagName=$1

repo_list='repo_list.txt'
while IFS= read -r repo; do
  git clone "${urlPrefix}${repo}"
  cd "${repo}" || exit 1
  git config user.name "${GITHUB_USERNAME}"
  result=$(git pull)
  RC=$?
  if [ $RC -ne 0 ]; then
    echo "$result"
    exit 1
  fi
  result=$(git tag | cat | grep 2021.xx)
  RC=$?
  if [[ $RC -ne 0 ]]; then
    echo "cannot grep 2021.07 so the tag does not exist"
    continue
  fi
  result=$(git push --delete origin 2021.xx)
  if [[ "$result" == *"does not exist"]]; then
    echo "Never Mind"
    continue
  fi
  RC=$?
  if [ $RC -ne 0 ]; then
    echo "$result"
    exit 1
  fi
  cd ..
done < "$repo_list"


