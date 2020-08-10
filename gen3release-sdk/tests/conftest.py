import pytest
import os


from gen3release.config import env

ABS_PATH = os.path.abspath(".")


@pytest.fixture(scope="function")
def source_env():
    return env.Env(ABS_PATH + "/data/fake_source_env")


@pytest.fixture(scope="function")
def target_env():
    return env.Env(ABS_PATH + "/data/fake_target_env")


@pytest.fixture()
def setUp_tearDown():
    os.system(f"mkdir {ABS_PATH}/data/temp_target_env")
    yield
    os.system(f"rm -r {ABS_PATH}/data/temp_target_env")
