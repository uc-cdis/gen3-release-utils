import hashlib
import shutil
from shutil import copytree, Error
import logging
import json
import os

LOGLEVEL = os.environ.get("LOGLEVEL", "DEBUG").upper()
logging.basicConfig(level=LOGLEVEL, format="%(asctime)-15s [%(levelname)s] %(message)s")
logging.getLogger(__name__)

def read_manifest(manifest):
  with open(manifest, 'r') as m:
    contents = m.read()
    return hashlib.md5(contents.encode('utf-8')), json.loads(contents)

def write_into_manifest(manifest, json_with_changes):
  with open(manifest, 'r+') as m:
    m.seek(0)
    m.write(json.dumps(json_with_changes, indent=2))
    m.truncate()
    return hashlib.md5(m.read().encode('utf-8'))

def recursive_copy(src, dst):
  os.chdir(src)
  for a_file in os.listdir():
    if a_file == 'README.md': continue
    logging.debug('copying file: {}'.format(a_file))
    if os.path.isdir(a_file):
      new_dst = os.path.join(dst, a_file)
      os.makedirs(new_dst, exist_ok=True)
      recursive_copy(os.path.abspath(a_file) + '/', new_dst)
    else:
      logging.debug('copying {} into {}'.format(a_file, dst))
      # files mapped in ENVIRONMENT_SPECIFIC_PARAMS need special treatment
      if a_file in ENVIRONMENT_SPECIFIC_PARAMS.keys():
        logging.debug('This file [{}] contains environment-specific \
  rameters that need to be saved.'.format(a_file))
        # remember environment-specific information
        env_params = load_environment_params(dst, a_file)
        shutil.copy(src + a_file, dst)
        logging.debug('Stored parameters: {}'.format(env_params))
        # re-apply all the stored environment-specific params
        merge_json_file_with_stored_environment_params(dst, a_file, env_params)
      else:
        shutil.copy(src + a_file, dst)
