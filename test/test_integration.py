import json
import requests

import constellation.docker_util as docker_util

from src import beebop_deploy


def test_start_beebop():
    # use a config that doesn't involve vault secrets
    cfg = beebop_deploy.BeebopConfig("config", "fake")
    obj = beebop_deploy.beebop_constellation(cfg)
    obj.status()
    obj.start()

    res = requests.get("https://localhost/api/", verify=False)

    assert res.status_code == 200
    assert json.loads(res.content)["message"] == "Welcome to beebop!"

    assert docker_util.network_exists("beebop_nw")
    assert docker_util.volume_exists("beebop_storage")
    assert docker_util.container_exists("beebop_api")
    assert docker_util.container_exists("beebop_redis")
    assert docker_util.container_exists("beebop_server")
    assert docker_util.container_exists("beebop_worker")
    assert docker_util.container_exists("beebop_proxy")

    obj.destroy()

    assert not docker_util.network_exists("beebop_nw")
    assert not docker_util.volume_exists("beebop_storage")
    assert not docker_util.container_exists("beebop_api")
    assert not docker_util.container_exists("beebop_redis")
    assert not docker_util.container_exists("beebop_server")
    assert not docker_util.container_exists("beebop_worker")
    assert not docker_util.container_exists("beebop_proxy")
