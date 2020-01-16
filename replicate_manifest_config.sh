#!/bin/bash

if [ "$1" == "-h" ] || [ "$1" == "--help" ] || [ "$#" -ne 2 ]; then
  echo "------------------------------------------------------------------------------"
  echo "Usage - replicate_manifest_config <source_manifest> <target_manifest>"
  echo ""
  echo "e.g., ./replicate_manifest_config.sh internalstaging.datastage.io/manifest.json gitops-qa/jenkins-dcp.planx-pla.net/manifest.json"
  echo ""
  echo "The script pulls data from a source manifest and replaces the versions & dictionary of the target manifest"
  echo "-------------------------------------------------------------------------------"
  exit 0;
fi;

svcs=(arborist fence indexd aws-es-proxy peregrine pidgin revproxy sheepdog portal fluentd spark tube manifestservice wts guppy sower hatchery ambassador)

# TODO: add "ssjdispatcher" "quay.io/cdis/ssjdispatcher:master" when modifying DEV/QA manifests 

# source manifest
# e.g., internalstaging.datastage.io/manifest.json
src_manifest="$1"
echo "fetching source manifest from: https://raw.githubusercontent.com/uc-cdis/cdis-manifest/master/${src_manifest}"
versions_and_dict=$(curl -s "https://raw.githubusercontent.com/uc-cdis/cdis-manifest/master/${src_manifest}" | jq '.versions, .global.dictionary_url')
# TODO: Error check here...

versions=$(echo "$versions_and_dict" | sed '$d')
new_dict=$(echo "$versions_and_dict" | tail -n1 | sed 's#/#\\/#g')

# target manifest
tgt_manifest="$2"

echo "testing"
svc="aws-es-proxy"
echo $versions | jq '.['\"${svc}\"']'

# replace all versions
for service in "${svcs[@]}"; do
  new_version=$(echo $versions | jq '.['\"${service}\"']' | sed 's#/#\\/#g')
  echo "applying version ${new_version} for ${service}"
  sed -i '.bak' "s/    \"${service}\": \".*,/    \"${service}\": ${new_version},/" $tgt_manifest
  # TODO: Err check
done

# replace dictionary
echo "applying new dictionary ${new_dict}..."
sed -i ".bak" "s/    \"dictionary_url\": \".*/    \"dictionary_url\": ${new_dict},/" $tgt_manifest
# TODO: err check

# remove backup file (rely on git)
echo "removing temp file..."
rm -rfv ${tgt_manifest}.bak

echo "done"
