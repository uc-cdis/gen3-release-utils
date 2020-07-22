from gen3release.config import env
import pytest
import json
import os


@pytest.fixture(scope="function")
def env_obj():
    return env.Env("./data/test_environment.$$&")


@pytest.fixture()
def manifest_data():
    data = None
    with open("./data/test_manifest.json", "r") as f:
        data = json.loads(f.read())
    return data


def test___init___():

    envobj = env.Env("./data/test_environment.$$&")
    assert envobj.name == "test_environment.$$&"
    assert envobj.repo_dir == "data"
    assert envobj.full_path == os.path.abspath("./data/test_environment.$$&")


def test_load_environment_params(env_obj):
    json_data = {
        "notes": ["These values should be loaded into env"],
        "global": {
            "environment": "A test env",  # VPC
            "hostname": "",
            "revproxy_arn": "",
            "kube_bucket": "kub buck",
            "logs_bucket": "some bucket",
            "sync_from_dbgap": "",
            "useryaml_s3path": "",
        },
        "hatchery": {
            "user-namespace": "a namespace",
            "sidecar": {
                "env": {"NAMESPACE": "blank", "HOSTNAME": "not blank"}
            },  # KUBE_NAMESPACE
        },
    }
    env_params = env_obj.ENVIRONMENT_SPECIFIC_PARAMS
    env_obj.load_environment_params("manifest.json", json_data)
    assert json_data.get("notes") == env_params["manifest.json"].get("notes")
    assert json_data.get("global") == env_params["manifest.json"].get("global")
    assert json_data.get("hatchery") == env_params["manifest.json"].get("hatchery")
    assert not env_params["manifest.json"].get("scaling")


def test_load_sower_jobs(env_obj):
    json_data = {
        "sower": [
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
                    {
                        "name": "creds-volume",
                        "secret": {"secretName": "sower-jobs-g3auto"},
                    }
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
                    {
                        "name": "creds-volume",
                        "secret": {"secretName": "sower-jobs-g3auto"},
                    }
                ],
                "restart_policy": "Never",
            },
        ]
    }
    env_obj.load_sower_jobs(json_data)
    sowersgot = json_data.get("sower_jobs")
    print(f"sowers got : {sowersgot}")
    assert env_obj.sower_jobs == json_data.get("sower")


def test_save_blocks(env_obj):
    data = {
        "scaling": {
            "arborist": {"strategy": "strat1", "min": 10, "max": 10, "targetCpu": 10},
            "fence": {"strategy": "strat2", "min": 10, "max": 10, "targetCpu": 10},
            "presigned-url-fence": {
                "strategy": "",
                "min": 10,
                "max": 10,
                "targetCpu": 10,
            },
            "indexd": {"strategy": "1", "min": 10, "max": 10, "targetCpu": 110},
            "revproxy": {"strategy": "1", "min": 10, "max": 10, "targetCpu": 10},
        },
    }

    mockenv_params = env_obj.ENVIRONMENT_SPECIFIC_PARAMS["manifest.json"]

    env_obj.save_blocks("scaling", mockenv_params, data)
    assert mockenv_params["scaling"] == data["scaling"]
