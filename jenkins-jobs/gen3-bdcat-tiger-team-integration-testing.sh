#!/bin/bash

# Run everyday at 5 PM UTC
# Schedule: H 17 * * *
# e.g., Would last have run at Wednesday, March 17, 2021 5:15:20 PM UTC; would next run at Thursday, March 18, 2021 5:15:20 PM UTC.

echo "Running the integration tests now..."

export CRYPTOGRAPHY_DONT_BUILD_RUST=1

# sed -i 's/google-resumable-media/google-resumable-media==v0.7.0/' requirements.txt
# sed -i 's/requests/requests==2.22.0/' requirements.txt

python3 -m pip install -r requirements.txt

python3 scripts/run_integration_tests.py
