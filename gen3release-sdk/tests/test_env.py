from gen3release.config import env
import pytest
import json

@pytest.fixture(scope="function")
def env_obj():
    return env.Env("./data/test_environment.$$&")

# def test___init__(): 
