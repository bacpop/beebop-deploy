import json
import requests
import urllib3
from requests.adapters import HTTPAdapter
import time
from requests.packages.urllib3.util.retry import Retry
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

    # Disable SSL warnings since we're using self-signed certs for testing
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Configure session with retries
    session = requests.Session()
    session.verify = False
    session.trust_env = False

    # Configure retry strategy
    retry_strategy = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)

    # Give services time to fully initialize
    time.sleep(2)

    # Make the request
    res = session.get("https://localhost/api/")

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
