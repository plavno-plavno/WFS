#!/bin/bash

# Set your Vast.ai API key
VAST_API_KEY="your_vast_api_key_here"

# Path to your SSH private key
SSH_KEY_PATH="$HOME/.ssh/id_rsa"

# Define the desired GPU type (e.g., "RTX 3090", "Tesla V100", "A100")
DESIRED_GPU_TYPE="RTX 3090"

# Define the template you want to use (e.g., Docker image, disk space, etc.)
TEMPLATE_IMAGE="ubuntu:20.04"
TEMPLATE_DISK_SIZE=50  # Disk size in GB

# Define the machine name to check for or assign to new instances
MACHINE_NAME="my_vast_machine"

# Custom command to run after updating the code
RESTART_SERVER_COMMAND="systemctl restart myserver"

# Command to run during initial setup of the machine
SETUP_COMMAND="apt update && apt install -y python3-pip && pip3 install -r requirements.txt"

# Ensure the SSH key path is correct
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo "Error: SSH key not found at $SSH_KEY_PATH."
    echo "Please make sure your SSH key exists or set the correct path."
    exit 1
fi

# Export the Vast.ai API key as an environment variable
export VAST_API_KEY="$VAST_API_KEY"

# Confirm that the Vast CLI is installed
if ! command -v vast &> /dev/null; then
    echo "Vast CLI could not be found. Please install it by running: pip install vast"
    exit 1
fi

# Step 1: Check if an existing instance with the desired machine name is already running
echo "Checking for an existing instance with the machine name: $MACHINE_NAME..."
EXISTING_INSTANCE=$(vast show instances | grep "$MACHINE_NAME" | awk '{print $1}')

if [ -n "$EXISTING_INSTANCE" ]; then
    echo "Found an existing instance with ID: $EXISTING_INSTANCE"

    # Get the SSH address of the existing instance
    EXISTING_INSTANCE_IP=$(vast show instance $EXISTING_INSTANCE | grep 'ssh:' | awk '{print $2}')

    if [ -z "$EXISTING_INSTANCE_IP" ]; then
        echo "Failed to fetch the SSH details of the existing instance. Exiting."
        exit 1
    fi

    echo "Existing instance SSH address: $EXISTING_INSTANCE_IP"

    # Step 2: Update the code on the existing instance using rsync
    echo "Updating code on the existing instance using rsync..."
    rsync -avz -e "ssh -i $SSH_KEY_PATH" ./ $EXISTING_INSTANCE_IP:~/app/

    # Step 3: Run the command to restart the server on the existing instance
    echo "Running command to restart the server on the existing instance..."
    ssh -i "$SSH_KEY_PATH" $EXISTING_INSTANCE_IP << EOF
        cd ~/app/
        $RESTART_SERVER_COMMAND
EOF

    echo "Server restarted successfully on the existing instance."
    exit 0
fi

# Step 4: No existing instance found, create a new one
echo "No existing instance found. Creating a new instance on Vast.ai..."

# Get a list of available machines with the desired GPU type
echo "Fetching a list of available machines with GPU type: $DESIRED_GPU_TYPE..."
vast search offers "gpu_name==$DESIRED_GPU_TYPE reliability > 0.98" > available_machines.txt

# Select the first machine from the list
MACHINE_ID=$(head -n 1 available_machines.txt | awk '{print $1}')

if [ -z "$MACHINE_ID" ]; then
    echo "No suitable machine found with GPU type: $DESIRED_GPU_TYPE. Please modify your search query or check Vast.ai."
    exit 1
fi

echo "Selected machine ID: $MACHINE_ID"

# Step 5: Create an instance on the chosen machine with the specified template and machine name
echo "Creating an instance on the chosen machine using template: $TEMPLATE_IMAGE with disk size: ${TEMPLATE_DISK_SIZE}GB..."
INSTANCE_ID=$(vast create instance $MACHINE_ID --image "$TEMPLATE_IMAGE" --disk $TEMPLATE_DISK_SIZE --volume-only --on-demand --name "$MACHINE_NAME")

if [ -z "$INSTANCE_ID" ]; then
    echo "Failed to create an instance on the machine. Exiting."
    exit 1
fi

echo "Instance ID created: $INSTANCE_ID"

# Step 6: Start the instance
echo "Starting the instance..."
vast start instance $INSTANCE_ID

# Step 7: Get the SSH details for the instance
echo "Fetching SSH details for the instance..."
INSTANCE_IP=$(vast show instance $INSTANCE_ID | grep 'ssh:' | awk '{print $2}')

if [ -z "$INSTANCE_IP" ]; then
    echo "Failed to fetch the SSH details. Exiting."
    exit 1
fi

echo "SSH address: $INSTANCE_IP"

# Step 8: Upload the current directory to the new instance using rsync
echo "Uploading current directory to the Docker machine on Vast.ai using rsync..."
rsync -avz -e "ssh -i $SSH_KEY_PATH" ./ $INSTANCE_IP:~/app/

# Step 9: SSH into the Docker machine and set up the environment
echo "Setting up environment on the machine..."
ssh -i "$SSH_KEY_PATH" $INSTANCE_IP << EOF
    cd ~/app/
    $SETUP_COMMAND
    echo "Setup complete. Ready to run your code."
EOF

echo "Done. You can now access your Vast.ai instance using: ssh -i $SSH_KEY_PATH $INSTANCE_IP"
