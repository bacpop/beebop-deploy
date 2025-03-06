set -eu
CONTAINER_NAME="beebop-api"
OUTPUT_FOLDER=/beebop/storage/poppunk_output
BACKUP_FOLDER=/beebop/storage/poppunk_output_backup

# Check if backup_folder exists inside the container
if docker exec $CONTAINER_NAME test -d $BACKUP_FOLDER; then
    # Remove output_folder and copy backup_folder to output_folder
    docker exec $CONTAINER_NAME rm -rf $OUTPUT_FOLDER
    docker exec $CONTAINER_NAME mv $BACKUP_FOLDER $OUTPUT_FOLDER
    echo "Successfully restored PopPUNK output from backup."
else
    echo "Backup folder $BACKUP_FOLDER does not exist inside the container."
fi

# Remove migration.py inside the container
docker exec $CONTAINER_NAME rm -f /beebop/storage/migration.py