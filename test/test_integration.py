import json
import requests
import os

import constellation.docker_util as docker_util

from src import beebop_deploy


def test_start_beebop():
    # use a config that doesn't involve vault secrets
    cfg = beebop_deploy.BeebopConfig("config", "fake")
    obj = beebop_deploy.beebop_constellation(cfg)
    obj.status()
    obj.start()

    assert docker_util.network_exists("beebop_nw")
    assert docker_util.volume_exists("beebop_storage")
    assert docker_util.volume_exists("redis-volume")
    assert docker_util.container_exists("beebop-api")
    assert docker_util.container_exists("beebop-redis")
    assert docker_util.container_exists("beebop-server")
    assert docker_util.container_exists("beebop-proxy")
    assert len(docker_util.containers_matching("beebop-worker-", False)) == 2

    # ignore SSL
    session = requests.Session()
    session.verify = False
    session.trust_env = False
    os.environ['CURL_CA_BUNDLE'] = ""
    res = session.get("https://localhost/api/", verify=False)

    assert res.status_code == 200
    assert json.loads(res.content)["message"] == "Welcome to beebop!"

    obj.destroy()

    assert not docker_util.network_exists("beebop_nw")
    assert not docker_util.volume_exists("beebop_storage")
    assert not docker_util.volume_exists("redis-volume")
    assert not docker_util.container_exists("beebop-api")
    assert not docker_util.container_exists("beebop-redis")
    assert not docker_util.container_exists("beebop-server")
    assert not docker_util.container_exists("beebop-worker")
    assert not docker_util.container_exists("beebop-proxy")
    assert len(docker_util.containers_matching("beebop-worker-", False)) == 0
