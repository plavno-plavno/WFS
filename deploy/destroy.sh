#!/bin/bash

# Load configuration
source deploy/config.sh
export VAST_API_KEY="$VAST_API_KEY"

echo "Checking for an existing instance with the machine label: $MACHINE_NAME..."
EXISTING_INSTANCE=$(vastai show instances | grep "$MACHINE_NAME" | awk '{print $1}')

if [ -n "$EXISTING_INSTANCE" ]; then
    echo "Found an existing instance with ID: $EXISTING_INSTANCE"
    vastai destroy instance $EXISTING_INSTANCE
    echo "Instance $EXISTING_INSTANCE destroyed."
else
    echo "No instance found with the machine label: $MACHINE_NAME."
fi
