#!/bin/bash
set -eu

# This script will set the species field to "Streptococcus pneumoniae" for all projects in the database

projectKeys=$(redis-cli --scan | grep -E ^beebop:project:[a-zA-Z0-9]+$)


echo "Number of found projects: $(echo "$projectKeys" | wc -w)"

for key in $projectKeys; do
    redis-cli HSET "$key" species "Streptococcus pneumoniae"
done