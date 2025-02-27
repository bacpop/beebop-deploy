#!/bin/bash
#!/bin/bash
set -eu
CONTAINER_NAME="beebop-api"
BACKUP_FOLDER=/beebop/storage/poppunk_output_backup

# Remove backup_folder inside the container if exists
if docker exec $CONTAINER_NAME test -d $BACKUP_FOLDER; then
    docker exec $CONTAINER_NAME rm -rf $BACKUP_FOLDER
    echo "Successfully restored PopPUNK output from backup."
else
    echo "Backup folder $BACKUP_FOLDER does not exist inside the container."
fi

# Remove migration.py inside the container
docker exec $CONTAINER_NAME rm -f /beebop/storage/migration.py
