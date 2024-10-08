# beebop-deploy
Deploy scripts for beebop

## Installation
Clone this repo and install dependencies with:
```
pip3 install --user -r requirements.txt
```

## Usage

```
Usage:
  ./beebop start [--pull] [<configname>]
  ./beebop stop  [--volumes] [--network] [--kill] [--force]
  ./beebop destroy
  ./beebop status
  ./beebop upgrade

Options:
  --pull                    Pull images before starting
  --volumes                 Remove volumes (WARNING: irreversible data loss)
  --network                 Remove network
  --kill                    Kill the containers (faster, but possible db corruption)
```

Once a configuration is set during `start`, it will be reused by subsequent commands 
(`stop`, `status`, `upgrade`, `user`, etc) and removed during destroy.
The configuration usage information is stored in `config/.last_deploy.`

## Deployment onto servers
We have one copy of `beebop` deployed:

* server: `beebop.dide.ic.ac.uk`
* config: `prod.yml`
* command to run: `./beebop start prod`

### Running data migrations

All data migrations are stored in the migration folder in the server. The naming convention is `YYYYMMDDHHMMSS_<migration_name>.sh`.

To run them, you can use the following command from the **root**, and replace the migration file with the one you want to run:

```bash
docker exec beebop-redis bash -c "$(cat ./migrations/<migration_file>)"

```
