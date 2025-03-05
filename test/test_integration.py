import json
import requests
import os
import urllib3
import ssl
import constellation.docker_util as docker_util

from src import beebop_deploy


def make_secure_request(url):
    """
    Make a secure request with comprehensive SSL handling

    Args:
        url (str): The URL to make the request to

    Returns:
        Response object from requests
    """
    # Disable SSL warnings (use cautiously)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    try:
        # Create a custom SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        # Create session with custom configuration
        session = requests.Session()
        session.verify = False  # Disable SSL verification

        # Make the request
        response = session.get(
            url,
            verify=False,  # Disable certificate verification
            timeout=10,  # Add a timeout to prevent hanging
        )

        return response

    except requests.exceptions.SSLError as ssl_error:
        print(f"SSL Error occurred: {ssl_error}")
        # Specific handling for SSL errors

    except requests.exceptions.RequestException as req_error:
        print(f"Request error occurred: {req_error}")
        # General request error handling

    return None


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
    os.environ["CURL_CA_BUNDLE"] = ""
    try:
        res = make_secure_request("https://localhost/api/")
        if res:
            print(f"Status Code: {res.status_code}")
            print(f"Response: {res.text}")
    except Exception as e:
        print(f"An error occurred: {e}")

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
