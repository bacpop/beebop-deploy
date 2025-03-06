#!/bin/bash
#!/bin/bash
set -eu
CONTAINER_NAME="beebop-api"
BACKUP_FOLDER=/beebop/storage/poppunk_output_backup

# Remove backup_folder inside the container if exists
if docker exec $CONTAINER_NAME test -d $BACKUP_FOLDER; then
    docker exec $CONTAINER_NAME rm -rf $BACKUP_FOLDER
    echo "Successfully cleaned up PopPUNK output from backup."
else
    echo "Backup folder $BACKUP_FOLDER does not exist inside the container."
fi

# Delete redis keys
docker cp cleanup_redis.py $CONTAINER_NAME:/beebop/storage
docker exec $CONTAINER_NAME python3 /beebop/storage/cleanup_redis.py

# Remove py scripts inside the container
docker exec $CONTAINER_NAME rm -f /beebop/storage/migration.py
docker exec $CONTAINER_NAME rm -f /beebop/storage/cleanup_redis.py
