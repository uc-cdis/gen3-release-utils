import pytest
import json
import hashlib
import os
import copy
import time

from ruamel.yaml import YAML

from gen3release.config import env
from gen3release.filesys import io_processing as py_io
from tests.helpers import are_dir_trees_equal
from tests.conftest import setUp_tearDown, target_env, target_env

ABS_PATH = os.path.abspath(".")


@pytest.fixture()
def loaded_target_env():

    obj = env.Env(ABS_PATH + "/data/fake_target_env")
    obj.sower_jobs = [
        {
            "name": "pelican-export",
            "action": "export",
            "container": {
                "name": "job-task",
                "image": "quay.io/cdis/pelican-export:2020.06",
                "pull_policy": "Always",
                "env": [
                    {
                        "name": "DICTIONARY_URL",
                        "valueFrom": {
                            "configMapKeyRef": {
                                "name": "manifest-global",
                                "key": "dictionary_url",
                            }
                        },
                    },
                    {
                        "name": "GEN3_HOSTNAME",
                        "valueFrom": {
                            "configMapKeyRef": {
                                "name": "manifest-global",
                                "key": "hostname",
                            }
                        },
                    },
                    {"name": "ROOT_NODE", "value": "subject"},
                ],
                "volumeMounts": [
                    {
                        "name": "pelican-creds-volume",
                        "readOnly": True,
                        "mountPath": "/pelican-creds.json",
                        "subPath": "config.json",
                    },
                    {
                        "name": "peregrine-creds-volume",
                        "readOnly": True,
                        "mountPath": "/peregrine-creds.json",
                        "subPath": "creds.json",
                    },
                ],
                "cpu-limit": "1",
                "memory-limit": "12Gi",
            },
            "volumes": [
                {
                    "name": "pelican-creds-volume",
                    "secret": {"secretName": "pelicanservice-g3auto"},
                },
                {
                    "name": "peregrine-creds-volume",
                    "secret": {"secretName": "peregrine-creds"},
                },
            ],
            "restart_policy": "Never",
        },
        {
            "name": "ingest-metadata-manifest",
            "action": "ingest-metadata-manifest",
            "activeDeadlineSeconds": 86400,
            "serviceAccountName": "jobs-fake_target_env",
            "container": {
                "name": "job-task",
                "image": "quay.io/cdis/metadata-manifest-ingestion:2.1.6",
                "pull_policy": "Always",
                "env": [
                    {
                        "name": "GEN3_HOSTNAME",
                        "valueFrom": {
                            "configMapKeyRef": {
                                "name": "manifest-global",
                                "key": "hostname",
                            }
                        },
                    }
                ],
                "volumeMounts": [
                    {
                        "name": "creds-volume",
                        "readOnly": True,
                        "mountPath": "/creds.json",
                        "subPath": "creds.json",
                    }
                ],
                "cpu-limit": "1",
                "memory-limit": "1Gi",
            },
            "volumes": [
                {"name": "creds-volume", "secret": {"secretName": "sower-jobs-g3auto"}}
            ],
            "restart_policy": "Never",
        },
        {
            "name": "get-dbgap-metadata",
            "action": "get-dbgap-metadata",
            "serviceAccountName": "jobs-fake_target_env",
            "container": {
                "name": "job-task",
                "image": "quay.io/cdis/get-dbgap-metadata:1.1.6",
                "pull_policy": "Always",
                "env": [],
                "volumeMounts": [
                    {
                        "name": "creds-volume",
                        "readOnly": True,
                        "mountPath": "/creds.json",
                        "subPath": "creds.json",
                    }
                ],
                "cpu-limit": "1",
                "memory-limit": "1Gi",
            },
            "volumes": [
                {"name": "creds-volume", "secret": {"secretName": "sower-jobs-g3auto"}}
            ],
            "restart_policy": "Never",
        },
    ]
    obj.environment_specific_params = {
        "manifest.json": {
            "notes": [
                "This is a fake target environment manifest",
                "That's all I have to say",
            ],
            "global": {
                "environment": "stageprod",  # VPC
                "hostname": "fake_target_env",
                "revproxy_arn": "arn:aws:acm:us-east-1:895962626746:certificate/a82bb5ed-9ad1-444d-9bfd-5bc314541307",
                "kube_bucket": "kube-stageprod-gen3",
                "logs_bucket": "logs-stageprod-gen3",
                "sync_from_dbgap": "true",
                "useryaml_s3path": "s3://cdis-gen3-users/stageprod/user.yaml",
            },
            "scaling": {
                "arborist": {"strategy": "auto", "min": 2, "max": 4, "targetCpu": 40},
                "fence": {"strategy": "auto", "min": 5, "max": 15, "targetCpu": 40},
                "presigned-url-fence": {
                    "strategy": "auto",
                    "min": 2,
                    "max": 5,
                    "targetCpu": 40,
                },
                "indexd": {"strategy": "auto", "min": 2, "max": 4, "targetCpu": 40},
                "revproxy": {"strategy": "auto", "min": 2, "max": 4, "targetCpu": 40},
            },
        },
        "hatchery.json": {
            "user-namespace": "jupyter-pods-fake_target_env",
            "sidecar": {
                "env": {
                    "NAMESPACE": "fake_target_env",
                    "HOSTNAME": "fake_target_env.datastage.io",
                }
            },
        },
    }
    return obj


@pytest.fixture()
def manifest_data():
    data = None
    with open(ABS_PATH + "/data/fake_target_env/manifest.json", "r") as f:
        data = json.loads(f.read())
    return data


@pytest.fixture()
def etlMapping_data():
    data = None
    with open(ABS_PATH + "/data/fake_target_env/etlMapping.yaml") as f:
        yaml = YAML(typ="safe")
        data = yaml.load(f)
    return data


def test_generate_safe_index_name():
    """
    Test that created names are valid index names
    """
    ENV_IN = [
        # test bad chars
        r"s\ngen\"3.b/iodatac\\atalyst. |n:<>hlbi.nih\n.go\v\n",
        # test bad chars in start
        r"\\gen\3.bi\foda\btac\atalyst.nhlbinih.gov",
        # test bad start chars
        r"--gen3.\/[bi/odatacatalyst].nhlbi.nih.gov",
        # test bad start chars and capital letters
        r"+\agen3.BIOdatacatalyst.nhlbi.nih.gov",
        # test 255 byte limit
        r"this_is_number_____________________________________________________________________________________________________________________________________________________________________________________________________________________________0123456789101112",
    ]
    ENV_OUT = [
        r"s_ngen__3.b_iodatac__atalyst.__n___hlbi.nih_n.go_v_n_testtype",
        r"gen_3.bi_foda_btac_atalyst.nhlbinih.gov_testtype",
        r"gen3.__[bi_odatacatalyst].nhlbi.nih.gov_testtype",
        r"agen3.biodatacatalyst.nhlbi.nih.gov_testtype",
        r"this_is_number_____________________________________________________________________________________________________________________________________________________________________________________________________________________________01234567891_testtype",
    ]
    for inp, oup, in zip(ENV_IN, ENV_OUT):
        print(f"input {inp}")
        output = py_io.generate_safe_index_name(inp, "testtype")
        print(f"output {output}")
        assert output == oup

    # Must have an environment name
    with pytest.raises(NameError):
        py_io.generate_safe_index_name("", "testtype")


def test_process_index_names(target_env, manifest_data, etlMapping_data):
    """
    Test that created names are correctly assigned to fields
    """
    # test names in manifest
    param_guppy = target_env.params_to_set["manifest.json"].get("guppy")
    file_guppy = manifest_data.get("guppy")
    py_io.process_index_names(
        target_env.name, param_guppy, file_guppy, "indices", "type", "index"
    )
    expected_guppy = {
        "indices": [
            {"index": "fake_target_env_subject", "type": "subject"},
            {"index": "fake_target_env_file", "type": "file"},
        ],
        "config_index": "fake_target_env_array-config",
        "auth_filter_field": "auth_resource_path",
    }
    assert file_guppy == expected_guppy

    # test names in etlMapping
    py_io.process_index_names(
        target_env.name,
        target_env.params_to_set["etlMapping.yaml"],
        etlMapping_data,
        "mappings",
        "doc_type",
        "name",
    )
    expected_yaml_names = ["fake_target_env_subject", "fake_target_env_file"]
    names = [d["name"] for d in etlMapping_data.get("mappings")]
    assert expected_yaml_names == names


def test_create_env_index_name(target_env, manifest_data, etlMapping_data):
    """
    Test that created names have the form <commonsname_type>
    """
    mani_data = py_io.create_env_index_name(target_env, "manifest.json", manifest_data)
    guppy = manifest_data.get("guppy")
    expected_guppy = {
        "indices": [
            {"index": "fake_target_env_subject", "type": "subject"},
            {"index": "fake_target_env_file", "type": "file"},
        ],
        "config_index": "fake_target_env_array-config",
        "auth_filter_field": "auth_resource_path",
    }
    assert guppy == expected_guppy

    yam_names = py_io.create_env_index_name(
        target_env, "etlMapping.yaml", etlMapping_data
    )
    expected_yaml_names = ["fake_target_env_subject", "fake_target_env_file"]
    names = [d["name"] for d in etlMapping_data.get("mappings")]
    assert expected_yaml_names == names


def test_write_index_names(target_env, setUp_tearDown):
    """
    Test that the files are updated with modified names
    """
    os.system(
        f"cp {ABS_PATH}/data/fake_target_env/manifest.json {ABS_PATH}/data/temp_target_env/manifest.json"
    )
    py_io.write_index_names(
        ABS_PATH + "/data",
        ABS_PATH + "/data/temp_target_env",
        "manifest.json",
        target_env,
    )
    os.chdir(ABS_PATH)
    with open(ABS_PATH + "/data/temp_target_env/manifest.json", "r") as f:
        with open(
            ABS_PATH + "/data/test_references/testnaming_manifest.json", "r"
        ) as f2:
            assert json.loads(f.read()) == json.loads(f2.read())


def test_store_environment_params(target_env, loaded_target_env):
    """
    Test that environment params are loaded into environment object
    """
    py_io.store_environment_params(
        ABS_PATH + "/data/fake_target_env", target_env, "manifest.json"
    )
    sowers = target_env.sower_jobs
    expected_sower = loaded_target_env.sower_jobs
    assert expected_sower == sowers
    env_params = target_env.environment_specific_params
    expected_params = loaded_target_env.environment_specific_params
    assert (
        expected_params["manifest.json"] == env_params["manifest.json"]
    ), f"Got: {env_params}"
    py_io.store_environment_params(
        ABS_PATH + "/data/fake_target_env/manifests/hatchery/",
        target_env,
        "hatchery.json",
    )
    assert expected_params["hatchery.json"] == env_params["hatchery.json"]


def test_read_manifest():
    """
    Test that different files have different hashes and same files have same hashes
    """
    hash1, json1 = py_io.read_manifest(ABS_PATH + "/data/fake_target_env/manifest.json")
    hash2, json2 = py_io.read_manifest(
        ABS_PATH + "/data/fake_target_env/manifests/hatchery/hatchery.json"
    )
    hash3, json3 = py_io.read_manifest(ABS_PATH + "/data/fake_target_env/manifest.json")
    assert hash1.digest() != hash2.digest()
    assert json1 != json2
    assert hash1.digest() == hash3.digest()
    assert json1 == json3


def test_merge():
    """
    Test that source dictionary is merged into target dictionary
    """
    src_dict_example = {
        "scaling": {
            "arborist": {"strategy": "", "min": 0, "max": 0, "targetCpu": 0},
            "fence": {"strategy": "", "min": 0, "max": 0, "targetCpu": 0},
            "presigned-url-fence": {"strategy": "", "max": 0, "targetCpu": 0,},
        }
    }
    tgt_dict_example = {
        "scaling": {
            "arborist": {"strategy": "auto", "min": 2, "max": 4, "targetCpu": 40},
            "fence": {"strategy": "auto", "min": 5, "max": 15, "targetCpu": 40},
            "presigned-url-fence": {
                "strategy": "auto",
                "min": 2,
                "max": 5,
                "targetCpu": 40,
            },
        }
    }
    tgt_merged = py_io.merge(src_dict_example, tgt_dict_example)
    expected_dict = {
        "scaling": {
            "arborist": {"strategy": "", "min": 0, "max": 0, "targetCpu": 0},
            "fence": {"strategy": "", "min": 0, "max": 0, "targetCpu": 0},
            "presigned-url-fence": {
                "strategy": "",
                "min": 2,
                "max": 0,
                "targetCpu": 0,
            },
        }
    }
    assert expected_dict == tgt_merged


def test_write_into_manifest(setUp_tearDown):
    """
    Test that a write was performed in the correct file
    """
    os.system(
        f"cp {ABS_PATH}/data/fake_target_env/manifest.json {ABS_PATH}/data/testing_manifest.json"
    )
    mod_time1 = os.path.getmtime(ABS_PATH + "/data/testing_manifest.json")
    time.sleep(0.001)
    py_io.write_into_manifest(ABS_PATH + "/data/testing_manifest.json", {})
    mod_time2 = os.path.getmtime(ABS_PATH + "/data/testing_manifest.json")
    os.system("rm ./data/testing_manifest.json")
    assert mod_time1 != mod_time2


def test_merge_json_file_with_stored_environment_params(target_env, loaded_target_env):
    """
    Test that manifest.json is written with correct enviroment params
    """
    os.system(
        f"cp {ABS_PATH}/data/fake_target_env/manifest.json {ABS_PATH}/data/manifest.json"
    )
    env_params = target_env.environment_specific_params["manifest.json"]
    print(env_params)
    py_io.merge_json_file_with_stored_environment_params(
        ABS_PATH + "/data", "manifest.json", env_params, target_env, loaded_target_env
    )

    with open(ABS_PATH + "/data/manifest.json", "r+") as f:
        with open(
            ABS_PATH + "/data/test_references/testmerge_manifest.json", "r"
        ) as f2:
            assert f2.read() == f.read()
    os.system("rm ./data/manifest.json")


def test_process_sower_jobs(target_env, loaded_target_env):
    """
    Test that sower jobs are not added to target if not already found in target
    """
    src = target_env
    tgt = loaded_target_env
    with open(ABS_PATH + "/data/fake_target_env/manifest.json", "r") as f:
        data = json.loads(f.read())
    assert data["sower"] != []
    print(target_env.sower_jobs)
    data = py_io.process_sower_jobs(data, src.sower_jobs, tgt.sower_jobs)
    assert data["sower"] == []

    # test target account name retained

    source_sower = [{"name": "fakejob", "serviceAccountName": "jobs-fake_source_env"}]
    tgt_sower = [{"name": "fakejob", "serviceAccountName": "jobs-fake_target_env"}]
    data = py_io.process_sower_jobs(data, source_sower, tgt_sower)
    assert data["sower"] == [
        {"name": "fakejob", "serviceAccountName": "jobs-fake_target_env"}
    ]


def test_recursive_copy(source_env, setUp_tearDown):
    """
    Test that all files and subfolders are copied from source env to target env
    """
    temp_tgt = env.Env(f"{ABS_PATH}/data/temp_target_env")
    files = py_io.recursive_copy(
        [], target_env, temp_tgt, source_env.full_path, temp_tgt.full_path
    )
    os.chdir(ABS_PATH)
    assert len(files) == 9
    assert are_dir_trees_equal(
        ABS_PATH + "/data/temp_target_env", ABS_PATH + "/data/fake_source_env"
    )
