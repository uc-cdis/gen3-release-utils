#!/bin/bash

# Schedule 0 0 * * *
# Runs on the gen3-qa-worker node
# Requires Jenkins secrets
#   GITHUB_USERNAME
#   GITHUB_TOKEN

#if [[ ! -d cdis-manifest ]]; then
#  git clone https://github.com/uc-cdis/cdis-manifest.git
#fi
#cd ./cdis-manifest
# List of commons to select from
git config --global user.email "cdis@uchicago.edu"
git config --global user.name "${GITHUB_USERNAME}"

urlPrefix="https://${GITHUB_USERNAME}:${GITHUB_TOKEN}@github.com/uc-cdis/"

git clone "${urlPrefix}cdis-manifest"
cd cdis-manifest

commons=("gen3.theanvil.io" "chicagoland.pandemicresponsecommons.org" "gen3.biodatacatalyst.nhlbi.nih.gov" "nci-crdc.datacommons.io" "data.braincommons.org" "vpodc.org")

# Select from one randomly
# TODO: We should cycle through each of them every night (TBD) -- This will pollute the cdis-manifest PRs screen so we should also .. CLOSE the PRs through a morning job :D
selectedCommons=${commons[$RANDOM % ${#commons[@]} ]}
# Log the commons selected
echo $selectedCommons
# Update the dictionary into a temp manifest, if you do it directly into the file it can end up empty
dictionaryUrl=$(cat $selectedCommons/manifest.json | jq -r .global.dictionary_url)
jq '.global.dictionary_url = '\"$dictionaryUrl\"'' nightly.planx-pla.net/manifest.json > nightly.planx-pla.net/manifest.json-tmp

# mutate other critical service-specific config blocks:
portalConfigBlock=$(cat chicagoland.pandemicresponsecommons.org/manifest.json | jq -r .portal)
jq --argjson obj '{"portal": '"$portalConfigBlock"'}' '. += $obj' < nightly.planx-pla.net/manifest.json-tmp > temp && mv temp nightly.planx-pla.net/manifest.json-tmp
sowerConfigBlock=$(cat chicagoland.pandemicresponsecommons.org/manifest.json | jq -r .sower)
jq --argjson obj '{"sower": '"$sowerConfigBlock"'}' '. += $obj' < nightly.planx-pla.net/manifest.json-tmp > temp && mv temp nightly.planx-pla.net/manifest.json-tmp

# set all sower jobs images to master
# with the quay img path as latest-master imgs are not automatically pushed to ECR
sed -i 's/\(.*\)\/gen3\/pelican-export:\(.*\)/quay.io\/cdis\/pelican-export:master",/' nightly.planx-pla.net/manifest.json-tmp
sed -i 's/\(.*\)\/gen3\/metadata-manifest-ingestion:\(.*\)/quay.io\/cdis\/metadata-manifest-ingestion:master",/' nightly.planx-pla.net/manifest.json-tmp
sed -i 's/\(.*\)\/gen3\/get-dbgap-metadata:\(.*\)/quay.io\/cdis\/get-dbgap-metadata:master",/' nightly.planx-pla.net/manifest.json-tmp
sed -i 's/\(.*\)\/gen3\/manifest-indexing:\(.*\)/quay.io\/cdis\/manifest-indexing:master",/' nightly.planx-pla.net/manifest.json-tmp
sed -i 's/\(.*\)\/gen3\/manifest-merging:\(.*\)/quay.io\/cdis\/manifest-merging:master",/' nightly.planx-pla.net/manifest.json-tmp
sed -i 's/\(.*\)\/gen3\/download-indexd-manifest:\(.*\)/quay.io\/cdis\/download-indexd-manifest:master",/' nightly.planx-pla.net/manifest.json-tmp

guppyConfigBlock=$(cat chicagoland.pandemicresponsecommons.org/manifest.json | jq -r .guppy)
jq --argjson obj '{"guppy": '"$guppyConfigBlock"'}' '. += $obj' < nightly.planx-pla.net/manifest.json-tmp > temp && mv temp nightly.planx-pla.net/manifest.json-tmp


# Add new special mutatedEnvHostname property to global block to facilitate the definition of testedEnd for testing purposes
jq --argjson obj '{"mutatedEnvHostname": "'"${selectedCommons}"'"}' '.global += $obj' < nightly.planx-pla.net/manifest.json-tmp > temp && mv temp nightly.planx-pla.net/manifest.json-tmp

# replace the manifest file with the temp one that has updated dictionary
mv nightly.planx-pla.net/manifest.json-tmp nightly.planx-pla.net/manifest.json
# delete old portal/etlmapping and pull from selected commons
rm -rf nightly.planx-pla.net/portal
rm nightly.planx-pla.net/etlMapping.yaml
cp -rf $selectedCommons/portal nightly.planx-pla.net/portal
cp $selectedCommons/etlMapping.yaml nightly.planx-pla.net/etlMapping.yaml
todaysDate=$(date '+%m-%d-%Y')

git checkout -b "Nightly($todaysDate)"
git add nightly.planx-pla.net
git commit -m "nightly build $todaysDate, using $selectedCommons"
git push origin "Nightly($todaysDate)"
number=$(curl -X POST "https://api.github.com/repos/uc-cdis/cdis-manifest/pulls" -H "Authorization: token $GITHUB_TOKEN" -H "Accept: application/vnd.github.v3+json" -d '{"head":"Nightly('$todaysDate')","base":"master", "title": "Nightly Build from '$todaysDate'"}' | jq -r .number)
curl -X PATCH "https://api.github.com/repos/uc-cdis/cdis-manifest/issues/$number" -H "Authorization: token $GITHUB_TOKEN" -H "Accept: application/vnd.github.v3+json" -d '{"labels": ["nightly-run"]}'
echo "Done"
