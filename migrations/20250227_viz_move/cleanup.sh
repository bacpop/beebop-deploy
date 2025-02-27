#!/bin/bash
set -eu
CONTAINER_NAME="beebop-api"

docker cp migration_cleanup.py $CONTAINER_NAME:/beebop/storage

docker exec $CONTAINER_NAME python /beebop/storage/migration_cleanup.py

# Remove migration.py inside the container
docker exec $CONTAINER_NAME rm -f /beebop/storage/migration.py
