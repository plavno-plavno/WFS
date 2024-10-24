#!/bin/bash

# Load configuration from config.sh
source ./config.sh

# Ensure the SSH key path is correct
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo "Error: SSH key not found at $SSH_KEY_PATH."
    echo "Please make sure your SSH key exists or set the correct path."
    echo "To generate a new SSH key pair, run the following command:"
    echo ""
    echo "    ssh-keygen -t rsa -b 4096 -C \"your_email@example.com\""
    echo ""
    echo "After running this command, follow the prompts to save the key as $SSH_KEY_PATH."
    echo "Once the key is generated, add it to your SSH agent with:"
    echo ""
    echo "    eval \$(ssh-agent -s)"
    echo "    ssh-add $SSH_KEY_PATH"
    exit 1
fi

# Export the Vast.ai API key as an environment variable
export VAST_API_KEY="$VAST_API_KEY"

# Check if the vastai CLI is installed, install it if not
if ! command -v vastai &> /dev/null; then
    echo "vastai CLI could not be found. Installing it using pip..."
    pip install --upgrade vastai
    if [ $? -ne 0 ]; then
        echo "Failed to install vastai CLI. Please check your Python and pip installation."
        exit 1
    fi
fi

# Step 1: Check if an existing instance with the desired machine name is already running
echo "Checking for an existing instance with the machine name: $MACHINE_NAME..."
EXISTING_INSTANCE=$(vastai show instances | grep "$MACHINE_NAME" | awk '{print $1}')

if [ -n "$EXISTING_INSTANCE" ]; then
    echo "Found an existing instance with ID: $EXISTING_INSTANCE"

    # Get the SSH address of the existing instance
    EXISTING_INSTANCE_IP=$(vastai show instance $EXISTING_INSTANCE | grep 'ssh:' | awk '{print $2}')

    if [ -z "$EXISTING_INSTANCE_IP" ]; then
        echo "Failed to fetch the SSH details of the existing instance. Exiting."
        exit 1
    fi

    echo "Existing instance SSH address: $EXISTING_INSTANCE_IP"

    # Step 2: Update the code on the existing instance using rsync
    echo "Updating code on the existing instance using rsync..."
    rsync -avz -e "ssh -i $SSH_KEY_PATH" ./ $EXISTING_INSTANCE_IP:$REMOTE_APP_DIR/

    # Step 3: Run the command to restart the server on the existing instance
    echo "Running command to restart the server on the existing instance..."
    ssh -i "$SSH_KEY_PATH" $EXISTING_INSTANCE_IP << EOF
        cd $REMOTE_APP_DIR/
        $RESTART_SERVER_COMMAND
EOF

    echo "Server restarted successfully on the existing instance."
    exit 0
fi

# Step 4: No existing instance found, create a new one
echo "No existing instance found. Creating a new instance on Vast.ai..."

# Get a list of available machines with the desired GPU type
echo "Fetching a list of available machines with GPU type: $DESIRED_GPU_TYPE..."
vastai search offers "gpu_name==$DESIRED_GPU_TYPE reliability > 0.98" > available_machines.txt

# Select the first machine from the list
MACHINE_ID=$(head -n 1 available_machines.txt | awk '{print $1}')

if [ -z "$MACHINE_ID" ]; then
    echo "No suitable machine found with GPU type: $DESIRED_GPU_TYPE. Please modify your search query or check Vast.ai."
    exit 1
fi

echo "Selected machine ID: $MACHINE_ID"

# Step 5: Create an instance on the chosen machine with the specified template and machine name
echo "Creating an instance on the chosen machine using template: $TEMPLATE_IMAGE with disk size: ${TEMPLATE_DISK_SIZE}GB..."
INSTANCE_ID=$(vastai create instance $MACHINE_ID --image "$TEMPLATE_IMAGE" --disk $TEMPLATE_DISK_SIZE --volume-only --on-demand --name "$MACHINE_NAME")

if [ -z "$INSTANCE_ID" ]; then
    echo "Failed to create an instance on the machine. Exiting."
    exit 1
fi

echo "Instance ID created: $INSTANCE_ID"

# Step 6: Start the instance
echo "Starting the instance..."
vastai start instance $INSTANCE_ID

# Step 7: Get the SSH details for the instance
echo "Fetching SSH details for the instance..."
INSTANCE_IP=$(vastai show instance $INSTANCE_ID | grep 'ssh:' | awk '{print $2}')

if [ -z "$INSTANCE_IP" ]; then
    echo "Failed to fetch the SSH details. Exiting."
    exit 1
fi

echo "SSH address: $INSTANCE_IP"

# Step 8: Upload the current directory to the new instance using rsync
echo "Uploading current directory to the Docker machine on Vast.ai using rsync..."
rsync -avz -e "ssh -i $SSH_KEY_PATH" ./ $INSTANCE_IP:$REMOTE_APP_DIR/

# Step 9: SSH into the Docker machine and set up the environment
echo "Setting up environment on the machine..."
ssh -i "$SSH_KEY_PATH" $INSTANCE_IP << EOF
    cd $REMOTE_APP_DIR/
    $SETUP_COMMAND
    echo "Setup complete. Ready to run your code."
EOF

echo "Done. You can now access your Vast.ai instance using: ssh -i $SSH_KEY_PATH $INSTANCE_IP"
