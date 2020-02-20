#!/bin/bash

#command line options
while getopts 'pd:' OPTION; do
  case "$OPTION" in
    p ) patch=true;;
    d ) dry=true;;
  esac
done
shift "$(($OPTIND - 1))"

username=$(git config user.name)
msg="$1 by $username"

#get the latest version
url="https://github.com/uc-cdis/"
repo_list="repo_list.txt"

while IFS= read -r repo; do
  b="$(git ls-remote --tags "${url}"/"${repo}" | sort -t "/" -k 3 -V | tail -1 | cut -d/ -f3-)"
  #sed -e
  echo "$repo" "$b"
done < "$repo_list" > tags.txt

#increase the version number
a=( ${version//./ } )

a[0]=$(date +'%Y')
a[1]=$(date +'%m')
a[2]=0

if [ ! -z "$patch" ]
then
  ((a[2]++))
fi

next_version="${a[0]}.${a[1]}.${a[2]}"
echo $next_version

if [ ! -z "$dry" ]
then
  echo "${next_version}"
else
  set -e
  for a in $(repo_list)
  do
    git checkout gen3-integration

    git tag -a "$next_version" -m "$msg"

    git push --tags origin stable

    echo -e "\e[32mRelease Done\e[0m"
  done
fi
