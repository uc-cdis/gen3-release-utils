# gen3-release-utils
Gen3 release process automation tools

# Overview

This repo hosts the `gen3release-sdk` and a few utility scripts used throughout a number of Jenkins jobs to facilitate the automation of the Gen3 Release efforts.

## Gen3 Release SDK

This solution aims to prevent human intervention / error-prone actions while performing Gen3 Release operations.

### Automatically creating Pull Requests for releases

The features of the SDK automate recurrent tasks, such as tailoring Pull Requests on github to:
- Deploy a given version to a target environment.
e.g.,
```
gen3release apply -v 2020.09 -e ~/workspace/cdis-manifest/gen3.biodatacatalyst.nhlbi.nih.gov
```
- Promote changes / Migrate artifacts from a non-prod tier environment to a customer-facing PROD environment (assuming testing has been conducted against the versions/ environmental configuration and QA has signed off on the changes).
e.g.,
```
gen3release copy -s ~/workspace/cdis-manifest/preprod.gen3.biodatacatalyst.nhlbi.nih.gov -e ~/workspace/cdis-manifest/gen3.biodatacatalyst.nhlbi.nih.gov
```

Theoretically (or perhaps, Utopically), we should eradicate all non-prod/staging:prod parity issues so we can raise confidence that whatever is tested in a pre-prod tier will work fine in PROD tiers. Hence, the solution should just make both set of artifacts across the environments match.

### Cloning environments

Another feature of the SDK tooling is to provide a Developer with the ability to "clone environments" or to make some DEV/QA environment impersonate a target PROD environment.

To better understand the need for such feature, one must be aware of the different types of environments we have and its correponding _tiers_:
- DEV (environment folders found in: https://github.com/uc-cdis/gitops-dev)
- QA  (environment folders found in: https://github.com/uc-cdis/gitops-qa)
- NON-PROD (environments prefixed with _preprod, internal staging or staging_ whose folders are found in: https://github.com/uc-cdis/cdis-manifest).
- PROD (environments named without the _preprod, internal staging or staging_ prefixes. whose folders are found in: https://github.com/uc-cdis/cdis-manifest).

There is some granularity between `internalstaging`,  which is internal, and `staging`, which is non-prod but externally facing (we let specific users access these staging environments so they can take a sneak peak at new features before rolling them out to prod or to keep some continuous cross-platform experiments).

The environment impersonation feature should help developers reproduce a bug and test potential fixes. e.g., Considering a fictitious scenario where a customer in a given PROD environment finds a bug with one of our sower jobs (e.g., manifest indexing). The manifest indexing feature relies on `ssjdispatcher`, `indexs3client`, `manifest-indexing`, the sower jobs config block and the `sower` service versions. In order to empower a Developer to configure his/her environment to reproduce this bug, they need to run the user flow and test the feature with the exact same configuration and versions from that target PROD environment. Therefore, the tool should look into the prod environment's folder in the `cdis-manifest` repo, copy all the version info + sower config from that target environment where the bug was found, and migrate / port that all the way back into an environment in `gitops-dev`/`gitops-qa` (any folder of the user's choice).

So the user of our `gen3release-sdk` will decide the _source environment_ based on their needs and the _target environment_ based on which dev environment he/she wants to use to impersonate a PROD environment for bug reproduction efforts (and also fix testing).

Which can be achieved with a command similar to:
```
gen3release copy -s cdis-manifest/gen3.biodatacatalyst.nhlbi.nih.gov -e gitops-dev/mattclark.planx-pla.net
```

## Other utility scripts

A few operations are still executed through Bash scripts (to be converted to `gen3release-sdk` features later), the following sections provide instructions on how to use them.

### Make new branches from existing ones

This utility is used to create integration and stable branches in multiple repos.

- How to use it:
    - Update `repo_list.txt` with the repositories where branches need to be created
    - Execute the script as follows:
    ```./make_branch.sh <sourceBranchName> <targetBranchName```

### Release Notes Generation

This utility uses the gen3git tool to generate release notes for Gen3 monthly releases

- How to use it:
    - Set environment variable GITHUB_TOKEN with your Github Personal Access Token
    - Install Python and [gen3git](https://github.com/uc-cdis/release-helper/) command line utility
    ```pip install --editable git+https://github.com/uc-cdis/release-helper.git@gen3release#egg=gen3git```
    - Update `repo_list.txt` with the repositories from which release notes need to be generated
    - Set the following environment variables in the terminal:
        - RELEASE_NAME - Release name e.g., `Core Gen3 Release 202006 (Edgewater)`
        - START_DATE - Start date in YYYY-MM-DD format
        - END_DATE - End date in YYYY-MM-DD format
        - GITHUB_TOKEN - Github personal access token
    - Execute generate_release_notes.sh
    ```./generate_release_notes.sh```

### LEGACY TOOLS
#### Manifest replication

This utility (replicate_manifest_config.sh) should facilitate the copy of versions (including dictionary_url, etc.) between `manifest.json` files, i.e., improving the release process so it will be more automated & less error-prone.

 - How to use it:
 Here is the syntax:
 > /bin/bash replicate_manifest_config.sh &lt;branch>/&lt;environment>/manifest.json &lt;target_manifest>

 Example:
 > % /bin/bash ../gen3-release-utils/replicate_manifest_config.sh master/internalstaging.datastage.io/manifest.json gen3.datastage.io/manifest.json
