#!/bin/bash

if [ "$1" == "-h" ] || [ "$1" == "--help" ] || [ "$#" -ne 2 ]; then
  echo "------------------------------------------------------------------------------"
  echo "Usage - gen3-config-diff <[repo/]namespace[:branch]> <[repo/]namespace[:branch]> [-(-m)anifest-only] [-(-p)ortal-only]"
  echo "e.g., gen3-config-diff gen3.datastage.io:stable gitops-qa/qa-datastage.planx-pla.net"
  echo ""
  echo "This script diffs the configurations of two or more gen3 commons."
  echo "NOTE: Requires jq https://stedolan.github.io/jq/"
  echo ""
  echo "If 'repo' is not specified, it is assumed to be 'cdis-manifest'." 
  echo "If 'branch' is not specified, it is assumed to be 'master'"
  echo "-------------------------------------------------------------------------------"
  exit 0;
fi;

github_url_base="https://raw.githubusercontent.com/uc-cdis"
default_branch="master"
default_repo="cdis-manifest"

# Iterate over arguments
while test ${#} -gt 0
do
  # Format: [repo/]namespace[:branch]
  # Parse the repo name, if any
  # Test for presence of a slash (/) in the part of the string before the colon, if any.
  if [[ $1 =~ ^[^:]*/.*$ ]]
    then
      # If there is a slash before a colon, everything before the slash is the repo name.
      repo=$(echo $1 | sed -r 's/^([^:]*)\/.*$/\1/')
      repo_specified=true
    else
      repo=$default_repo
  fi
  echo "repo: $repo"

  # Parse the branch name, if any
  # Test for presence of a colon(':') in the string
  if [[ $1 == *:* ]]
    then 
      # If there is a colon, everything after the colon is the branch name
      branch=$(echo $1 | sed -r 's/.*:(.*)$/\1/')
      # Replace leading underscore with forward slash('/'), in case anyone tries to use
      # the quay branch syntax (e.g. feat_newfeature instead of feat/newfeature)
      branch=$(echo $branch | sed 's/_/\//' )
      branch_specified=true
    else
      branch=$default_branch
  fi
  echo "branch: $branch"

  # Parse commons namespace
  namespace=$1
  # If the repo was specified, remove the repo name from the front of the argument
  if [[ repo_specified ]]
    then
      namespace=$(echo $namespace | sed -r "s/$repo\/(.*)/\1/")
  fi
  # Remove the branch name if present
  namespace=$(echo $namespace | sed -r 's/^([^:]*):?.*$/\1/')
  echo "namespace:$namespace"

  # Create the base URL
  url="$github_url_base/$repo/$branch/$namespace"
  echo $url

  shift
done

# # Insert branch between repo and 'manifest.json', i.e. <repo>/master/<namespace>/manifest.json
# manifest_A_branch=master
# manifest_A_path=manifest.json
# manifest_A_path=$(echo $1 | sed "s_\(.*\)/\(.*\)_\1/$manifest_A_branch/\2/$manifest_A_path_")
# # TODO: Error check here...
# manifest_A_url="$github_url_base$manifest_A_path"
# echo "fetching manifest A from: ${manifest_A_url}"
# manifest_A_raw=$(curl -s "$manifest_A_url")
# # TODO: Error check here...
# # Sort keys and prettify json
# manifest_A=$(jq -S "." <(echo "$manifest_A_raw"))
# # TODO move 'versions' to top

# vimdiff <(echo "$manifest_A") <(echo "$manifest_B")

# echo "done"
