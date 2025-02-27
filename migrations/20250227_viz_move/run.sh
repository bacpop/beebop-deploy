#!/bin/bash
set -eu

CONTAINER_NAME="beebop-api"

docker cp migration.py $CONTAINER_NAME:/beebop/storage

docker exec $CONTAINER_NAME python3 /beebop/storage/migration.py