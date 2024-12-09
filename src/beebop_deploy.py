import time
import os

import docker
import json
import constellation
import constellation.config as config
import constellation.docker_util as docker_util


class BeebopConfig:
    def __init__(self, path, config_name=None, options=None):
        dat = config.read_yaml("{}/beebop.yml".format(path))
        dat = config.config_build(path, dat, config_name, options=options)
        self.path = path
        self.data = dat
        self.vault = config.config_vault(dat, ["vault"])
        self.network = config.config_string(dat, ["docker", "network"])
        self.container_prefix = config.config_string(dat, ["docker", "prefix"])
        self.registry = config.config_string(dat, ["docker", "registry"])
        self.download_ref_dbs_only = config.config_boolean(
            dat, ["download_ref_dbs_only"], is_optional=True, default=False
        )

        self.containers = {
            "redis": "redis",
            "api": "api",
            "server": "server",
            "proxy": "proxy",
            "worker": "worker"
        }

        self.volumes = {
            "storage": "beebop_storage",
            "redis-volume": "redis-volume",
        }

        # redis
        redis_name = config.config_string(
            dat, ["redis", "image", "name"])
        redis_tag = config.config_string(dat, ["redis", "image", "tag"])
        self.redis_ref = constellation.ImageReference(
            "library", redis_name, redis_tag)

        # proxy
        proxy_repo = config.config_string(
            dat, ["proxy", "image", "repo"])
        proxy_name = config.config_string(
            dat, ["proxy", "image", "name"])
        proxy_tag = config.config_string(
            dat, ["proxy", "image", "tag"])
        self.proxy_ref = constellation.ImageReference(
            f"{self.registry}/{proxy_repo}", proxy_name, proxy_tag)
        self.proxy_host = config.config_string(dat, ["proxy", "host"])
        self.proxy_port_http = config.config_integer(dat,
                                                     ["proxy", "port_http"])
        self.proxy_port_https = config.config_integer(dat,
                                                      ["proxy", "port_https"])
        if "ssl" in dat["proxy"]:
            self.proxy_ssl_certificate = config.config_string(dat,
                                                              ["proxy",
                                                               "ssl",
                                                               "certificate"])
            self.proxy_ssl_key = config.config_string(dat,
                                                      ["proxy",
                                                       "ssl",
                                                       "key"])
            self.ssl = True
        else:
            self.ssl = False

        # server
        server_repo = config.config_string(
            dat, ["server", "image", "repo"])
        server_name = config.config_string(
            dat, ["server", "image", "name"])
        server_tag = config.config_string(
            dat, ["server", "image", "tag"])
        self.server_ref = constellation.ImageReference(
            f"{self.registry}/{server_repo}", server_name, server_tag)
        self.server_port = config.config_integer(dat, ["server", "port"])
        self.client_url = config.config_string(dat, ["server", "client_url"])
        self.server_url = config.config_string(dat, ["server", "server_url"])
        self.redis_url = config.config_string(dat, ["server", "redis_url"])
        self.google_client_id = config.config_string(
            dat, ["server", "auth", "google", "client_id"])
        self.google_client_secret = config.config_string(
            dat, ["server", "auth", "google", "secret"])
        self.github_client_id = config.config_string(
            dat, ["server", "auth", "github", "client_id"])
        self.github_client_secret = config.config_string(
            dat, ["server", "auth", "github", "secret"])
        self.session_secret = config.config_string(
            dat, ["server", "auth", "session_secret"])

        # api
        api_repo = config.config_string(
            dat, ["api", "image", "repo"])
        api_name = config.config_string(
            dat, ["api", "image", "name"])
        api_tag = config.config_string(
            dat, ["api", "image", "tag"])
        self.api_ref = constellation.ImageReference(
            f"{self.registry}/{api_repo}", api_name, api_tag)
        self.api_storage_location = config.config_string(
            dat, ["api", "storage_location"])
        self.api_dbs_location = config.config_string(
            dat, ["api", "dbs_location"])

        # worker and api the same image
        self.worker_ref = constellation.ImageReference(
            f"{self.registry}/{api_repo}", api_name, api_tag)
        self.worker_count = config.config_integer(dat, ["worker", "count"])


def beebop_constellation(cfg):
    # 1. redis
    redis_mounts = [constellation.ConstellationMount("redis-volume", "/data")]
    redis = constellation.ConstellationContainer(
        "redis", cfg.redis_ref, configure=redis_configure, mounts=redis_mounts
    )

    # 2. api
    api_env = {"REDIS_HOST": redis.name,
               "STORAGE_LOCATION": cfg.api_storage_location,
               "DBS_LOCATION": cfg.api_dbs_location}
    api_mounts = [constellation.ConstellationMount("storage",
                                                   "/beebop/storage")]
    api = constellation.ConstellationContainer(
        "api", cfg.api_ref, environment=api_env, mounts=api_mounts,
        configure=api_configure)

    # 3. server
    server = constellation.ConstellationContainer(
        "server", cfg.server_ref, configure=server_configure(api))

    # 4. worker
    worker_env = {"REDIS_HOST": redis.name}
    worker_mounts = [constellation.ConstellationMount("storage",
                                                      "/beebop/storage")]
    # Constellation starts containers on no network, then joins them to
    # the network. So we get the container to sleep for 5s to allow for it
    # to have joined the network by the time rqworker is called, otherwise
    # it exits when it can't connect to redis
    worker_args = ["-c", "sleep 5 && rqworker"]
    worker = constellation.ConstellationService(
        "worker", cfg.worker_ref, cfg.worker_count, environment=worker_env,
        mounts=worker_mounts, entrypoint="sh", args=worker_args)

    # 5. proxy
    proxy_ports = [cfg.proxy_port_http, cfg.proxy_port_https]
    proxy = constellation.ConstellationContainer(
        "proxy", cfg.proxy_ref, ports=proxy_ports, configure=proxy_configure,
        args=[cfg.proxy_host,
              server.name])

    containers = [redis, server, api, proxy, worker]

    obj = constellation.Constellation("beebop", cfg.container_prefix,
                                      containers,
                                      cfg.network, cfg.volumes,
                                      data=cfg, vault_config=cfg.vault)
    return obj


def beebop_start(obj, args):
    obj.start(**args)


def redis_configure(container, cfg):
    print("[redis] Waiting for redis to come up")
    docker_util.file_into_container(
        "scripts/wait_for_redis", container, ".", "wait_for_redis")
    docker_util.exec_safely(container, ["bash", "/wait_for_redis"])


def api_configure(container, cfg):
    print("[api] Downloading storage database")
    args = ["./scripts/download_databases"]
    if cfg.download_ref_dbs_only:
        args.append("--refs")
    mounts = [docker.types.Mount("/beebop/storage", cfg.volumes["storage"])]
    container.client.containers.run(
        str(cfg.api_ref), args, mounts=mounts, remove=True
    )


def server_configure(api):
    def configure(container, cfg):
        print("[beebop] Configuring beebop server")
        config = {
            "server_port": cfg.server_port,
            "api_url": "http://{}:5000".format(api.name),
            "client_url": cfg.client_url,
            "server_url": cfg.server_url,
            "redis_url": cfg.redis_url,
            "GOOGLE_CLIENT_ID": cfg.google_client_id,
            "GOOGLE_CLIENT_SECRET": cfg.google_client_secret,
            "GITHUB_CLIENT_ID": cfg.github_client_id,
            "GITHUB_CLIENT_SECRET": cfg.github_client_secret,
            "SESSION_SECRET": cfg.session_secret
        }

        docker_util.string_into_container(json.dumps(config), container,
                                          "/app/src/resources/config.json")

    return configure


def proxy_configure(container, cfg):
    print("[proxy] Configuring proxy")
    if cfg.ssl:
        print("Copying ssl certificate and key into proxy")
        docker_util.string_into_container(cfg.proxy_ssl_certificate, container,
                                          "/run/proxy/certificate.pem")
        docker_util.string_into_container(cfg.proxy_ssl_key, container,
                                          "/run/proxy/key.pem")
    else:
        print("Generating self-signed certificates for proxy")
        args = ["/usr/local/bin/build-self-signed-certificate", "/run/proxy",
                "GB", "London", "IC", "bacpop", cfg.proxy_host]
        docker_util.exec_safely(container, args)
