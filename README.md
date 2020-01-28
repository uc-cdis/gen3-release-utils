# gen3-release-utils
Gen3 release process automation tools


# Manifest replication

This utility (replicate_manifest_config.sh) should facilitate the copy of versions (including dictionary_url, etc.) between `manifest.json` files, i.e., improving the release process so it will be more automated & less error-prone.

 - How to use it:
 Here is the syntax:
 > /bin/bash replicate_manifest_config.sh &lt;branch>/&lt;environment>/manifest.json &lt;target_manifest>

 Example:
 > % /bin/bash ../gen3-release-utils/replicate_manifest_config.sh master/internalstaging.datastage.io/manifest.json gen3.datastage.io/manifest.json
