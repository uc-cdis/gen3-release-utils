#!/bin/bash

current_folder=$(echo $PWD | awk -F "/" '{print $NF}')
if [ "$current_folder" != "gitops-qa" ]; then
    echo "please run this script from the root folder of your Gitops QA workspace. e.g., cd ~/workspace/gitops-qa and then run: bash ../gen3-release-utils"
    exit 1
fi

if [ "$1" == "-h" ] || [ "$1" == "--help" ] || [ "$#" -ne 1 ]; then
  echo "------------------------------------------------------------------------------"
  echo "Usage - apply_release_to_qa_envs <release tag>"
  echo ""
  echo "e.g., bash ../gen3-release-utils/apply_release_to_qa_envs.sh 2020.02"
  echo ""
  echo "This should replicate all the versions defined in the source release manifest (e.g., master/releases/2020/02/manifest.json)"
  echo "-------------------------------------------------------------------------------"
  exit 0;
fi;

# TODO: add "ssjdispatcher" "quay.io/cdis/ssjdispatcher:master" when modifying DEV/QA manifests 

# assemble path to the manifest
release_tag=$1
path_to_release_manifest=master/releases/$(echo $release_tag | tr "." "/")/manifest.json

echo "path_to_release_manifest: $path_to_release_manifest"

# source manifest
src_manifest="https://raw.githubusercontent.com/uc-cdis/cdis-manifest/$path_to_release_manifest"
# e.g., https://raw.githubusercontent.com/uc-cdis/cdis-manifest/master/releases/2020/02/manifest.json

echo "fetching source manifest from: ${src_manifest}"
versions_and_dict=$(curl -s "$src_manifest" | jq '.versions, .global.dictionary_url')
# TODO: Error check here...

versions=$(echo "$versions_and_dict" | sed '$d')
new_dict=$(echo "$versions_and_dict" | tail -n1 | sed 's#/#\\/#g')

# iterate through all the qa environments
ls_qa_envs=($(ls -l | awk '{ print $NF }' | grep "qa-*" | tr "\n" " "))

# assemble list of services
svcs=($(echo $versions | jq '. | keys' | sed '1d;$d' | tr "," " " | xargs))

for qa_env_folder in "${ls_qa_envs[@]}"; do
  # target manifest
  tgt_manifest="$qa_env_folder/manifest.json"

  # replace all versions
  for service in "${svcs[@]}"; do
    if [ "$service" == "revproxy" ]; then
      continue
    fi
    new_version=$(echo $versions | jq '.['\"${service}\"']' | sed 's#/#\\/#g')
    echo "applying version ${new_version} for ${service} in ${qa_env_folder}"
    sed -i '.bak' "s/    \"${service}\": \".*,/    \"${service}\": ${new_version},/" $tgt_manifest
    # TODO: Err check
  done

  # remove backup file (rely on git)
  echo "removing temp file..."
  rm -rfv ${tgt_manifest}.bak

done

echo "done"
