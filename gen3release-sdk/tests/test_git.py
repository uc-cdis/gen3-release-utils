from gen3release.gith.git import Git as gh
import pytest
from github.Repository import Repository


@pytest.fixture()
def ghub():
    return gh(repo="cdis-manifest")


def test_get_github_client(ghub):
    repo = ghub.get_github_client()
    assert type(repo) == Repository
    assert repo.git_url == "git://github.com/uc-cdis/cdis-manifest.git"
