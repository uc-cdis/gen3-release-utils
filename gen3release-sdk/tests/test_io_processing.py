from gen3release.filesys import io_processing as py_io
import pytest
from gen3release.config import env
import json
from ruamel.yaml import YAML
import hashlib
import os
import copy
from tests.helpers import are_dir_trees_equal
import hashlib

absolutepath = os.path.abspath(".")


@pytest.fixture(scope="function")
def env_obj():
    return env.Env(absolutepath + "/data/test_environment.$$&")


@pytest.fixture()
def loaded_env_obj():
    obj = env.Env(absolutepath + "/data/test_environment.$$&")
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
            "serviceAccountName": "jobs-preprod-gen3-biodatacatalyst-nhlbi-nih-gov",
            "container": {
                "name": "job-task",
                "image": "quay.io/cdis/metadata-manifest-ingestion:1.1.6",
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
            "serviceAccountName": "jobs-preprod-gen3-biodatacatalyst-nhlbi-nih-gov",
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
        {
            "name": "manifest-indexing",
            "action": "index-object-manifest",
            "activeDeadlineSeconds": 86400,
            "serviceAccountName": "jobs-preprod-gen3-biodatacatalyst-nhlbi-nih-gov",
            "container": {
                "name": "job-task",
                "image": "quay.io/cdis/manifest-indexing:1.1.6",
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
                        "name": "sower-jobs-creds-volume",
                        "readOnly": True,
                        "mountPath": "/creds.json",
                        "subPath": "creds.json",
                    }
                ],
                "cpu-limit": "1",
                "memory-limit": "1Gi",
            },
            "volumes": [
                {
                    "name": "sower-jobs-creds-volume",
                    "secret": {"secretName": "sower-jobs-g3auto"},
                }
            ],
            "restart_policy": "Never",
        },
        {
            "name": "indexd-manifest",
            "action": "download-indexd-manifest",
            "activeDeadlineSeconds": 86400,
            "serviceAccountName": "jobs-preprod-gen3-biodatacatalyst-nhlbi-nih-gov",
            "container": {
                "name": "job-task",
                "image": "quay.io/cdis/download-indexd-manifest:1.1.6",
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
                        "name": "sower-jobs-creds-volume",
                        "readOnly": True,
                        "mountPath": "/creds.json",
                        "subPath": "creds.json",
                    }
                ],
                "cpu-limit": "1",
                "memory-limit": "1Gi",
            },
            "volumes": [
                {
                    "name": "sower-jobs-creds-volume",
                    "secret": {"secretName": "sower-jobs-g3auto"},
                }
            ],
            "restart_policy": "Never",
        },
    ]
    obj.ENVIRONMENT_SPECIFIC_PARAMS = {
        "manifest.json": {
            "notes": [
                "This is the internalstaging environment manifest",
                "That's all I have to say",
            ],
            "global": {
                "environment": "stageprod",  # VPC
                "hostname": "test_environment.$$&",
                "revproxy_arn": "arn:aws:acm:us-east-1:895962626746:certificate/a82bb5ed-9ad1-444d-9bfd-5bc314541307",
                "kube_bucket": "kube-stageprod-gen3",
                "logs_bucket": "logs-stageprod-gen3",
                "sync_from_dbgap": "True",
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
            "user-namespace": "jupyter-pods-internalstaging",
            "sidecar": {
                "env": {
                    "NAMESPACE": "internalstaging",
                    "HOSTNAME": "internalstaging.datastage.io",
                }
            },
        },
    }
    return obj


@pytest.fixture()
def manifest_data():
    data = None
    with open(absolutepath + "/data/test_manifest.json", "r") as f:
        data = json.loads(f.read())
    return data


@pytest.fixture()
def etlMapping_data():
    data = None
    with open(absolutepath + "/data/test_etlMapping.yaml") as f:
        yaml = YAML(typ="safe")
        data = yaml.load(f)
    return data

    # def test_generate_safe_index_name():

    ENV_IN = [
        r"s\ngen3.b/iodatac\\atalyst.nhlbi.nih\n.go\v\n",
        r"\\gen\3.bi\foda\btac\atalyst.nhlbinih.gov",
        r"--gen3.\/[bi/odatacatalyst].nhlbi.nih.gov",
        r"+\agen3.biodatacatalyst.nhlbi.nih.gov",
        r"this_is_number_____________________________________________________________________________________________________________________________________________________________________________________________________________________________0123456789101112",
    ]
    ENV_OUT = [
        r"s_ngen3.b_iodatac__atalyst.nhlbi.nih_n.go_v_n_testtype",
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
    with pytest.raises(NameError):
        py_io.generate_safe_index_name("", "testtype")


def test_process_index_names(env_obj, manifest_data, etlMapping_data):
    param_guppy = env_obj.PARAMS_TO_SET["manifest.json"].get("guppy")
    file_guppy = manifest_data.get("guppy")
    py_io.process_index_names(
        env_obj.name, param_guppy, file_guppy, "indices", "type", "index"
    )
    expected_guppy = {
        "indices": [
            {"index": "test_environment.$$&_subject", "type": "subject"},
            {"index": "test_environment.$$&_file", "type": "file"},
        ],
        "config_index": "internalstaging_array-config",
        "auth_filter_field": "auth_resource_path",
    }
    assert file_guppy == expected_guppy
    py_io.process_index_names(
        env_obj.name,
        env_obj.PARAMS_TO_SET["etlMapping.yaml"],
        etlMapping_data,
        "mappings",
        "doc_type",
        "name",
    )
    expected_yaml_names = ["test_environment.$$&_subject", "test_environment.$$&_file"]
    names = [d["name"] for d in etlMapping_data.get("mappings")]
    assert expected_yaml_names == names


def test_create_env_index_name(env_obj, manifest_data, etlMapping_data):
    mani_data = py_io.create_env_index_name(env_obj, "manifest.json", manifest_data)
    guppy = manifest_data.get("guppy")
    expected_guppy = {
        "indices": [
            {"index": "test_environment.$$&_subject", "type": "subject"},
            {"index": "test_environment.$$&_file", "type": "file"},
        ],
        "config_index": "test_environment.$$&_array-config",
        "auth_filter_field": "auth_resource_path",
    }
    assert guppy == expected_guppy

    yam_names = py_io.create_env_index_name(env_obj, "etlMapping.yaml", etlMapping_data)
    expected_yaml_names = ["test_environment.$$&_subject", "test_environment.$$&_file"]
    names = [d["name"] for d in etlMapping_data.get("mappings")]
    assert expected_yaml_names == names


def test_write_index_names(env_obj):
    os.system(f"mkdir {absolutepath}/data/temp")
    os.system(
        f"cp {absolutepath}/data/test_manifest.json {absolutepath}/data/temp/manifest.json"
    )
    py_io.write_index_names(
        absolutepath + "/data", absolutepath + "/data/temp", "manifest.json", env_obj
    )
    os.chdir(absolutepath)
    shahash1 = hashlib.sha1()
    shahash2 = hashlib.sha1()
    with open(absolutepath + "/data/temp/manifest.json", "r") as f:
        for l in f:
            shahash1.update(l.encode("utf-8"))
    with open(absolutepath + "/data/testnaming_manifest.json", "r") as f2:
        for l in f2:
            shahash2.update(l.encode("utf-8"))

    os.system(
        f"diff {absolutepath}/data/temp/manifest.json {absolutepath}/data/testnaming_manifest.json"
    )
    assert shahash1.digest() == shahash2.digest()
    os.system(f"rm -r {absolutepath}/data/temp")


def test_store_environment_params(env_obj, loaded_env_obj):
    py_io.store_environment_params(
        absolutepath + "/data/test_environment.$$&", env_obj, "manifest.json"
    )
    sowers = env_obj.sower_jobs
    expected_sower = loaded_env_obj.sower_jobs
    assert expected_sower == sowers
    env_params = env_obj.ENVIRONMENT_SPECIFIC_PARAMS
    expected_params = loaded_env_obj.ENVIRONMENT_SPECIFIC_PARAMS
    assert (
        expected_params["manifest.json"] == env_params["manifest.json"]
    ), f"Got: {env_params}"
    py_io.store_environment_params(
        absolutepath + "/data/test_environment.$$&/manifests/hatchery/",
        env_obj,
        "hatchery.json",
    )
    assert expected_params["hatchery.json"] == env_params["hatchery.json"]


def test_read_manifest():
    hash1, json1 = py_io.read_manifest(
        absolutepath + "/data/test_environment.$$&/manifest.json"
    )
    hash2, json2 = py_io.read_manifest(
        absolutepath + "/data/test_environment.$$&/manifests/hatchery/hatchery.json"
    )
    hash3, json3 = py_io.read_manifest(
        absolutepath + "/data/test_environment.$$&/manifest.json"
    )
    assert hash1.digest() != hash2.digest()
    assert json1 != json2
    assert hash1.digest() == hash3.digest()
    assert json1 == json3


def test_merge():
    dict1 = {
        "scaling": {
            "arborist": {"strategy": "", "min": 0, "max": 0, "targetCpu": 0},
            "fence": {"strategy": "", "min": 0, "max": 0, "targetCpu": 0},
            "presigned-url-fence": {"strategy": "", "max": 0, "targetCpu": 0,},
        }
    }
    dict2 = {
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
    dict3 = py_io.merge(dict1, dict2)
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
    assert expected_dict == dict3


def test_write_into_manifest():
    os.system(
        f"cp {absolutepath}/data/test_manifest.json {absolutepath}/data/testing_manifest.json"
    )
    with open(absolutepath + "/data/testing_manifest.json", "r") as f:
        hash1 = hashlib.md5(f.read().encode("utf-8")).digest()
    hash2 = py_io.write_into_manifest(
        absolutepath + "/data/testing_manifest.json", {}
    ).digest()
    assert hash1 != hash2
    os.system("rm ./data/testing_manifest.json")


def test_merge_json_file_with_stored_environment_params(env_obj, loaded_env_obj):
    os.system(
        f"cp {absolutepath}/data/test_manifest.json {absolutepath}/data/manifest.json"
    )
    env_params = env_obj.ENVIRONMENT_SPECIFIC_PARAMS["manifest.json"]
    print(env_params)
    py_io.merge_json_file_with_stored_environment_params(
        absolutepath + "/data", "manifest.json", env_params, env_obj, loaded_env_obj
    )

    with open(absolutepath + "/data/manifest.json", "r+") as f:
        with open(absolutepath + "/data/testmerge_manifest.json", "r") as f2:
            assert f2.read() == f.read()
    os.system("rm ./data/manifest.json")


def test_remove_superfluous_sower_jobs(env_obj, loaded_env_obj):
    with open(absolutepath + "/data/test_manifest.json", "r") as f:
        data = json.loads(f.read())
    assert data["sower"] != []
    print(env_obj.sower_jobs)
    py_io.remove_superfluous_sower_jobs(
        data, env_obj.sower_jobs, loaded_env_obj.sower_jobs
    )
    assert data["sower"] == []


def test_recursive_copy(env_obj):
    curr = os.curdir
    fullpath = os.path.abspath(curr)
    os.system(f"mkdir {absolutepath}/data/temp")
    temp_env = env.Env(f"{absolutepath}/data/temp")
    files = py_io.recursive_copy(
        [], env_obj, temp_env, env_obj.full_path, temp_env.full_path
    )
    os.chdir(fullpath)
    assert len(files) == 9
    assert are_dir_trees_equal(
        absolutepath + "/data/temp", absolutepath + "/data/test_environment.$$&"
    )
    os.system(f"rm -r {absolutepath}/data/temp")
