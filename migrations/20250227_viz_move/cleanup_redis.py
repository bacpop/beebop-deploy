import redis
import logging


def main(logger):
    logger.info("Removing Redis keys...")
    r = redis.Redis(host="beebop-redis")

    if r.exists("beebop:hash:job:microreact"):
        r.delete("beebop:hash:job:microreact")
        logger.info("Successfully deleted key 'beebop:hash:job:microreact'")

    microreact_cluster_keys = r.keys("beebop:hash:job:microreact:*")
    for key in microreact_cluster_keys:
        r.delete(key)
        logger.info(f"Successfully deleted key {key.decode('utf-8')}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    main(logger)
