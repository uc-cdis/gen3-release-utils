#!/bin/bash +x

# Runs every Tuesday (right before the Wednesday QA Weekly Review meeting)
# Schedule: H 21 * * 2
# Would last have run at Tuesday, March 16, 2021 9:47:46 PM UTC; would next run at Tuesday, March 23, 2021 9:47:46 PM UTC.

git clone https://github.com/uc-cdis/gen3-qa.git

cd gen3-qa

export KUBECTL_NAMESPACE="default"
node --version
npm install
node generate-test-plan.js
