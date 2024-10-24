# config.sh

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

# Define the destination folder on the remote machine
REMOTE_APP_DIR="~/app"
