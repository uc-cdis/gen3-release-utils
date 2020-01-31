#!/bin/bash

if [ "$1" == "-h" ] || [ "$1" == "--help" ] || [ "$#" -ne 2 ]; then
  echo "------------------------------------------------------------------------------"
  echo "Usage - manifest-diff <repo/namespace> <repo/namespace>"
  echo ""
  echo "e.g., ./manifest-diff.sh cdis-manifest/internalstaging.datastage.io gitops-qa/jenkins-dcp.planx-pla.net"
  echo ""
  echo "The script diffs two manifests. It pulls the latest (master) versions of both manifests from https://github.com/uc-cdis/."
  echo "NOTE: Requires jq to be installed."
  echo "-------------------------------------------------------------------------------"
  exit 0;
fi;

github_url_base="https://raw.githubusercontent.com/uc-cdis/"

# Format of $1 is "<repo>/<namespace>" e.g., "cdis-manifest/internalstaging.datastage.io"
# Insert branch 'master' and 'manifest.json', i.e. <repo>/master/<namespace>/manifest.json
manifest_A_path=$(echo $1 | sed 's_\(.*\)/\(.*\)_\1/master/\2/manifest.json_')
# TODO: Error check here...
manifest_A_url="$github_url_base$manifest_A_path"
echo "fetching manifest A from: ${manifest_A_url}"
manifest_A_raw=$(curl -s "$manifest_A_url")
# TODO: Error check here...
manifest_A=$(jq -S "." <(echo "$manifest_A_raw"))

manifest_B_path=$(echo $2 | sed 's_\(.*\)/\(.*\)_\1/master/\2/manifest.json_')
# TODO: Error check here...
manifest_B_url="$github_url_base$manifest_B_path"
echo "fetching manifest A from: ${manifest_B_url}"
manifest_B_raw=$(curl -s "$manifest_B_url")
# TODO: Error check here...
manifest_B=$(jq -S "." <(echo "$manifest_B_raw"))

 
vimdiff <(echo "$manifest_A") <(echo "$manifest_B")

echo "done"
