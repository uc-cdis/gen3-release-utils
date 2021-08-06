#!/bin/bash -x

# String parameter SOURCE_USER_YAML
#   e.g., commons-users/users/datastageinternalstaging/user.yaml

# String parameter TARGET_USER_YAML
#   e.g., datastage-users/users/stageprod/user.yaml

export PATH=$PATH:/var/jenkins_home/.local/bin:/var/jenkins_home/.local/lib:/home/jenkins/.local/bin
python3.8 -m pip install poetry --user

python3.8 -m pip uninstall gen3release -y

cd gen3release-sdk
python3.8 -m poetry build

# TODO: Why are we doing this instead of poetry install and poetry run?
wheel_file=$(ls dist | grep whl | tail -n1)

python3.8 -m pip install dist/${wheel_file} --user

gen3release users -s ${SOURCE_USER_YAML} -t ${TARGET_USER_YAML}
