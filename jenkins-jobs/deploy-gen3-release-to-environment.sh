#!/bin/bash -x

# String parameter RELEASE_VERSION
#   e.g., 2021.04

# String parameter PR_TITLE
#   Default value: Gen3 Monthly Release

# String parameter TARGET_ENVIRONMENT
#   e.g., acct.bionimbus.org

# String parameter REPO_NAME
#   Default value: cdis-manifest

# GITHUB_TOKEN
# Obtained through Jenkins credentials

if [ -z "$TARGET_ENVIRONMENT" ]
then echo "Error: TARGET_ENVIRONMENT is empty!"
exit 1
fi

git clone https://github.com/uc-cdis/${REPO_NAME}.git

export PATH=$PATH:/var/jenkins_home/.local/bin:/var/jenkins_home/.local/lib:/home/jenkins/.local/bin
python3 -m pip install poetry --user

# TODO: Why are we doing this instead of poetry install and poetry run?
python3 -m pip install pygithub --user

python3 -m pip uninstall gen3release -y

cd gen3release-sdk
python3 -m poetry build

ls dist | grep whl | tail -n1
wheel_file=$(ls dist | grep whl | tail -n1)

poetry install

# TODO: TO NOT DO THIS
# Inject ECR img paths for all components
ls_quay_imgs=($(cat ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT}/manifest.json| jq .versions | grep "quay.io/cdis" | awk '{ print $1 }' | tr ":" " " | xargs)); for quay_img in "${ls_quay_imgs[@]}"; do if [[ "${quay_img}" == "aws-es-proxy" ]]; then continue; fi; cat ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT}/manifest.json | jq -c --arg ecr_path "707767160287.dkr.ecr.us-east-1.amazonaws.com/gen3/${quay_img}:${RELEASE_VERSION}" --arg jq_quay_img "$quay_img" '.versions[$jq_quay_img] = $ecr_path' | jq > $WORKSPACE/manifest.json.tmp && mv $WORKSPACE/manifest.json.tmp ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT}/manifest.json; done
sed -i 's/\/metadata:202/\/metadata-service:202/' ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT}/manifest.json
sed -i 's/dashboard:202/gen3-statics:202/' ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT}/manifest.json
sed -i 's/datareplicate:/dcf-dataservice:/' ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT}/manifest.json
sed -i 's/\/spark:202/\/gen3-spark:202/' ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT}/manifest.json
sed -i 's/revproxy:202/nginx:202/' ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT}/manifest.json
sed -i 's/\/portal:202/\/data-portal:202/' ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT}/manifest.json
sed -i 's/wts:202/workspace-token-service:202/' ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT}/manifest.json
sed -i 's/quay.io\/cdis\/gen3fuse-sidecar:202/707767160287.dkr.ecr.us-east-1.amazonaws.com\/gen3\/gen3fuse-sidecar:202/' ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT}/manifests/hatchery/hatchery.json

sed -i 's/quay.io\/cdis\/indexs3client:202/707767160287.dkr.ecr.us-east-1.amazonaws.com\/gen3\/indexs3client:202/' ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT}/manifest.json
sed -i 's/quay.io\/cdis\/pelican-export:202/707767160287.dkr.ecr.us-east-1.amazonaws.com\/gen3\/pelican-export:202/' ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT}/manifest.json
sed -i 's/quay.io\/cdis\/metadata-manifest-ingestion:202/707767160287.dkr.ecr.us-east-1.amazonaws.com\/gen3\/metadata-manifest-ingestion:202/' ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT}/manifest.json
sed -i 's/quay.io\/cdis\/get-dbgap-metadata:202/707767160287.dkr.ecr.us-east-1.amazonaws.com\/gen3\/get-dbgap-metadata:202/' ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT}/manifest.json
sed -i 's/quay.io\/cdis\/manifest-indexing:202/707767160287.dkr.ecr.us-east-1.amazonaws.com\/gen3\/manifest-indexing:202/' ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT}/manifest.json
sed -i 's/quay.io\/cdis\/manifest-merging:202/707767160287.dkr.ecr.us-east-1.amazonaws.com\/gen3\/manifest-merging:202/' ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT}/manifest.json
sed -i 's/quay.io\/cdis\/download-indexd-manifest:202/707767160287.dkr.ecr.us-east-1.amazonaws.com\/gen3\/download-indexd-manifest:202/' ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT}/manifest.json


cat ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT}/manifest.json

poetry run gen3release apply -v $RELEASE_VERSION -e ${WORKSPACE}/${REPO_NAME}/${TARGET_ENVIRONMENT} -pr "${PR_TITLE} ${RELEASE_VERSION} ${TARGET_ENVIRONMENT} $(date +%s)"
