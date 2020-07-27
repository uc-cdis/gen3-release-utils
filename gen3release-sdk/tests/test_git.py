from gen3release.gith.git import Git as gh
import pytest
from github.Repository import Repository
from unittest.mock import Mock, patch, call
from gen3release.config import env


@pytest.fixture()
def ghub():
    return gh(repo="cdis-manifest")


@pytest.fixture()
def mock_repo():
    return Mock(spec=Repository)


@pytest.fixture(scope="function")
def env_obj():
    return env.Env("./data/test_environment.$$&")


def test_get_github_client(ghub):
    repo = ghub.get_github_client()
    assert type(repo) == Repository
    assert repo.git_url == "git://github.com/uc-cdis/cdis-manifest.git"


def test_cut_new_branch(ghub, mock_repo):
    mock_repo.get_branch = Mock()
    git_ref = ghub.cut_new_branch(mock_repo, "new_branch_name")
    mock_repo.get_branch.assert_called_with("master")
    mock_repo.create_git_ref.assert_called_with(
        ref="refs/heads/new_branch_name", sha=mock_repo.get_branch().commit.sha
    )


def test_create_pull_request_copy(ghub, env_obj, mock_repo):
    ghub.create_pull_request_copy(
        mock_repo,
        env_obj,
        env_obj,
        ["etlMapping.yaml", "manifest.json"],
        "testpr",
        "commit message",
        "new_branch_name",
    )
    expected_args = [
        call("test_environment.$$&/etlMapping.yaml", "new_branch_name"),
        call("test_environment.$$&/manifest.json", "new_branch_name"),
    ]
    assert expected_args == mock_repo.get_contents.call_args_list
    data1 = open("./data/test_environment.$$&/etlMapping.yaml", "rb")
    data2 = open("./data/test_environment.$$&/manifest.json", "rb")
    expct_args = [
        call(
            "test_environment.$$&/etlMapping.yaml",
            "copying etlMapping.yaml to test_environment.$$&",
            data1.read(),
            mock_repo.get_contents().sha,
            branch="new_branch_name",
        ),
        call(
            "test_environment.$$&/manifest.json",
            "copying manifest.json to test_environment.$$&",
            data2.read(),
            mock_repo.get_contents().sha,
            branch="new_branch_name",
        ),
    ]

    assert expct_args == mock_repo.update_file.call_args_list
    data1.close()
    data2.close()

    mock_repo.create_pull.assert_called_with(
        title="testpr", body="commit message", head="new_branch_name", base="master"
    )
