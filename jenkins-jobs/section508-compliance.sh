#!/bin/bash

# checkout gen3-qa (branch: */chore/biodatacatalyst_section_508)

# String parameter TARGET_GEN3_ENVIRONMENT
#   e.g., gen3.datastage.io

# String parameter GUIDE
#   e.g., 508
#   Description: Choices: 508, WCAG1-A, WCAG1-AA, WCAG1-AAA, WCAG2-A, WCAG2-AA, WCAG2-AAA, BITV1, STANCA Default: WCAG2-AA
#     The accessbility guideline to validate against.

# CTDS_QA_ACHECKER
# Obtained through Jenkins credentials

echo "check AChecker: ${CTDS_QA_ACHECKER}"
bash scripts/section508_compliance.sh
