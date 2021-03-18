#!/bin/bash

# JENKINS_USER_API_TOKEN
# Obtained through Jenkins credentials

# Archive qa-metrics-all.json

ls -ilha files

python3.6 files/metrics.py
