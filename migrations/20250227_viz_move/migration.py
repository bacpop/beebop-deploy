import os
import shutil
import re
import redis
import logging


def setup_logging():
    """Configure logging for the migration script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("migration")


def create_backups(base_folder, logger):
    """Create backups of all output folders before migration."""
    logger.info("Creating backups of output folders...")

    # Get all valid output folders
    all_output_folders = [
        os.path.join(base_folder, item)
        for item in os.listdir(base_folder)
        if os.path.isdir(os.path.join(base_folder, item))
    ]

    # Filter for folders with network folder (i.e old output folders to update)
    output_folders = [
        folder
        for folder in all_output_folders
        if os.path.exists(os.path.join(folder, "network"))
    ]

    for folder_path in output_folders:
        dest_folder = folder_path + "_backup"
        if not os.path.exists(dest_folder):
            shutil.copytree(folder_path, dest_folder)
            logger.info(f"Created backup: {dest_folder}")

    return output_folders


def update_redis_keys(logger):
    """Update Redis job keys to match new structure."""
    logger.info("Updating Redis keys...")
    r = redis.Redis(host="beebop-redis")

    # Rename the Redis key from "beebop:hash:job:microreact" to "beebop:hash:job:visualise"
    if r.exists("beebop:hash:job:microreact"):
        microreact_data = r.hgetall("beebop:hash:job:microreact")
        for field, value in microreact_data.items():
            r.hset("beebop:hash:job:visualise", field, value)
        logger.info(
            "Successfully renamed key from 'beebop:hash:job:microreact' to 'beebop:hash:job:visualise'"
        )

    else:
        logger.info("Source key 'beebop:hash:job:microreact' does not exist")

    # Rename the Redis keys for each cluster
    microreact_cluster_keys = r.keys("beebop:hash:job:microreact:*")
    for key in microreact_cluster_keys:
        phash = key.decode("utf-8").split(":")[-1]
        microreact_data = r.hgetall(key)
        for field, value in microreact_data.items():
            r.hset(f"beebop:hash:job:visualise:{phash}", field, value)
        # r.delete(key)  # Delete the old Redis key after renaming
        print(f"Successfully renamed key from 'beebop:hash:job:microreact:{phash}' to 'beebop:hash:job:visualise:{phash}'")


def get_all_folders(output_folders):
    """Get all subdirectories for processing."""
    all_folders = []
    for folder_path in output_folders:
        for root, dirs, files in os.walk(folder_path):
            for dir in dirs:
                all_folders.append(os.path.join(root, dir))
    return all_folders


def add_pruned_graphmls(all_folders, logger):
    """Add pruned graphml files if not already present."""
    logger.info("Adding pruned graphml files...")
    for folder_path in all_folders:
        folder_name = os.path.basename(folder_path)
        if folder_name == "network":
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    if file.startswith("network_component"):
                        new_file_name = file.replace(
                            "network_component", "pruned_network_component"
                        )
                        new_file = os.path.join(folder_path, new_file_name)
                        if not os.path.exists(new_file):
                            logger.info(
                                f"Copying {file} to pruned version {new_file_name}"
                            )
                            shutil.copyfile(
                                os.path.join(folder_path, file), new_file
                            )
                        else:
                            logger.info(
                                f"Pruned version of {file} already exists"
                            )


def rename_microreact_to_visualise(all_folders, logger):
    """Rename microreact folders and files to visualise."""
    logger.info("Renaming microreact folders and files to visualise...")
    updated_folders = all_folders.copy()

    for i, folder_path in enumerate(all_folders):
        folder_name = os.path.basename(folder_path)
        if folder_name.startswith("microreact_"):
            new_folder_name = folder_name.replace("microreact_", "visualise_")
            new_folder_path = os.path.join(
                os.path.dirname(folder_path), new_folder_name
            )
            if not os.path.exists(new_folder_path):
                os.rename(folder_path, new_folder_path)
                logger.info(
                    f"Renamed folder: {folder_name} → {new_folder_name}"
                )
                # Update the folder path in the list
                updated_folders[i] = new_folder_path

            # Rename files within the folder
            for root, dirs, files in os.walk(new_folder_path):
                for file in files:
                    if file.startswith("microreact_"):
                        new_file_name = file.replace(
                            "microreact_", "visualise_", 1
                        )
                        new_file = os.path.join(root, new_file_name)
                        old_file = os.path.join(root, file)
                        if not os.path.exists(new_file):
                            os.rename(old_file, new_file)
                            logger.info(
                                f"Renamed file: {file} → {new_file_name}"
                            )

    return updated_folders


def move_network_files_to_visualise(all_folders, logger):
    """Move network files to visualise folders."""
    logger.info("Moving network files to visualise folders...")
    for folder_path in all_folders:
        folder_name = os.path.basename(folder_path)
        if folder_name == "network":
            parent_folder = os.path.dirname(folder_path)

            # Process CSV files
            move_csv_files(folder_path, parent_folder, logger)

            # Process GraphML files
            move_graphml_files(folder_path, parent_folder, logger)


def move_csv_files(network_folder, parent_folder, logger):
    """Move CSV files from network folder to visualise folders."""
    for file in os.listdir(network_folder):
        if file.endswith(".csv"):
            for dir_name in os.listdir(parent_folder):
                if os.path.isdir(
                    os.path.join(parent_folder, dir_name)
                ) and dir_name.startswith("visualise_"):
                    # Rename file
                    new_fname = file.replace("network", dir_name)
                    new_fname_path = os.path.join(network_folder, new_fname)

                    if not os.path.exists(new_fname_path):
                        shutil.copyfile(
                            os.path.join(network_folder, file), new_fname_path
                        )
                        logger.info(f"Copied file: {file} → {new_fname}")

                    # Move file to visualise folder
                    visualise_folder = os.path.join(parent_folder, dir_name)
                    shutil.move(new_fname_path, visualise_folder)
                    logger.info(
                        f"Moved file: {new_fname} → {visualise_folder}"
                    )


def move_graphml_files(network_folder, parent_folder, logger):
    """Move GraphML files from network folder to visualise folders."""
    for file in os.listdir(network_folder):
        if file.endswith(".graphml"):
            # Get lowest cluster number (assigned cluster)
            cluster_nums = re.findall(r"\d+", file)
            if not cluster_nums:
                logger.warning(f"No cluster numbers found in {file}")
                continue

            cluster_num = min(map(int, cluster_nums))
            visualise_dir = f"visualise_{cluster_num}"
            visualise_path = os.path.join(parent_folder, visualise_dir)

            if os.path.exists(visualise_path):
                new_fname = file.replace("network", visualise_dir)
                new_fname_path = os.path.join(network_folder, new_fname)

                if not os.path.exists(new_fname_path):
                    os.rename(
                        os.path.join(network_folder, file), new_fname_path
                    )
                    logger.info(f"Renamed file: {file} → {new_fname}")

                # Move file to visualise folder
                shutil.move(new_fname_path, visualise_path)
                logger.info(f"Moved file: {new_fname} → {visualise_path}")


def main():
    """Main function to orchestrate the migration."""
    logger = setup_logging()
    logger.info("Starting data migration script")

    base_folder = "poppunk_output"

    # Step 1: Create backups
    output_folders = create_backups(base_folder, logger)

    # Step 2: Update Redis keys
    update_redis_keys(logger)

    # Step 3: Get all folders for processing
    all_folders = get_all_folders(output_folders)

    # Step 4: Add pruned GraphML files
    add_pruned_graphmls(all_folders, logger)

    # Step 5: Rename microreact to visualise
    updated_all_folders = rename_microreact_to_visualise(all_folders, logger)

    # Step 6: Move network files to visualise folders
    move_network_files_to_visualise(updated_all_folders, logger)

    logger.info("Migration completed successfully")


if __name__ == "__main__":
    main()
