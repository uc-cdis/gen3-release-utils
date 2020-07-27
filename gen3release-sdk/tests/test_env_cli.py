from gen3release import env_cli
from gen3release.config.env import Env
from gen3release.env_cli import Gh

import pytest
import json
import os
import argparse
from argparse import Namespace
from unittest.mock import Mock, patch, call
from github.Repository import Repository
from tests.helpers import are_dir_trees_equal

fullpath_wd = os.path.abspath(".")


def test_make_parser():
    parser = env_cli.make_parser()
    args = parser.parse_args(
        [
            "copy",
            "-s",
            "/home/usr/demo/environment1",
            "-e",
            "/home/usr/demo/environment2",
        ]
    )
    assert args.env == "/home/usr/demo/environment2"
    assert args.func == env_cli.copy
    parser2 = env_cli.make_parser()
    args = parser2.parse_args(
        ["apply", "-v", "/home/usr/demo/environment1", "-e", "/home/usr/demo/targetenv"]
    )
    assert args.env == "/home/usr/demo/targetenv"
    assert args.func == env_cli.apply


@patch("gen3release.env_cli.Gh")
@patch("gen3release.env_cli.time")
@patch("gen3release.env_cli.copy_all_files")
@patch("gen3release.env_cli.Env")
def test_copy(mocked_env, copyfiles, mockedtime, mockedGh):

    os.system(f"mkdir {fullpath_wd}/data/temp")
    args_pr = Namespace(
        source=fullpath_wd + "/data/test_environment.$$&",
        env=fullpath_wd + "/data/temp",
        pr_title="A pr title",
    )
    copyfiles.return_value = ["file_1", "file_2"]
    mockedtime.time.return_value = "10.0"
    mocked_env.return_value.repo_dir = "./data"
    mocked_env.return_value.name = "env"
    env_cli.copy(args_pr)
    assert mocked_env.call_args_list == [call(args_pr.source), call(args_pr.env)]
    mockedGh.assert_called_with(repo="data")
    mockedGh.return_value.cut_new_branch.assert_called_once()
    mockedGh.return_value.create_pull_request_copy.assert_called_with(
        mockedGh.return_value.get_github_client.return_value,
        mocked_env(),
        mocked_env(),
        ["file_1", "file_2"],
        args_pr.pr_title,
        "copying files from env to env",
        "chore/promote_env_10",
    )
    os.system(f"rm -r {fullpath_wd}/data/temp")


def test_copy_all_files():
    with pytest.raises(NameError):
        s = Env("./fakepath")
        t = Env("./fakepath")
        env_cli.copy_all_files(s, t)
    os.system(f"mkdir {fullpath_wd}/data/temp")
    src = Env("./data/test_environment.$$&")
    tgt = Env("./data/temp")
    files = env_cli.copy_all_files(src, tgt)
    expected_files = [
        "portal/gitops-sponsors/nhlbi.png",
        "portal/gitops-logo.png",
        "portal/gitops-favicon.ico",
        "portal/gitops.css",
        "portal/gitops.json",
        "etlMapping.yaml",
        "manifest.json",
        "manifests/fence/fence-config-public.yaml",
        "manifests/hatchery/hatchery.json",
    ]
    assert sorted(files) == sorted(expected_files)
    os.system(f"rm -r {fullpath_wd}/data/temp")
