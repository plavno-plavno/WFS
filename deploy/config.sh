#!/bin/bash
set -e  # Exit immediately if a command exits with a non-zero status

# Function to clean domain names
clean_domain_name() {
    local domain="$1"
    # Remove all characters except letters, numbers, dots, and hyphens
    local clean_domain=$(echo "$domain" | sed 's/[^a-zA-Z0-9.-]//g')
    echo "$clean_domain"
}

# Set your Vast.ai API key (Consider using environment variables or a secure method)
VAST_API_KEY="bf299128b308697749900f6b3b6c9f758b35b9a5f4a33c1c71b5fad44d237231"
export VAST_API_KEY

# Path to your SSH private key
SSH_KEY_PATH="$HOME/.ssh/rsa_vast"
echo "$SSH_KEY_PATH"

# Define the machine name to check for or assign to new instances
MACHINE_NAME="a100"

# Define the desired GPU type and amount
DESIRED_GPU_TYPE="RTX_4090"  # e.g., "RTX 3090", "Tesla V100", "A100"
DESIRED_GPU_AMOUNT=1

EMAIL='info@plavno.app'

# Cloudflare Zone ID
ZONE_ID="ada507ed941aef5e37fc25de7eab42dd"

# Cloudflare API Key for Bearer authentication (Consider using environment variables or a secure method)
CLOUDFLARE_API_KEY="O6m_4-d8CRQqVr9z3yJQMUtNgDEaBw6SI2anuiTd"

# Define the template for instance creation
TEMPLATE_IMAGE="pytorch/pytorch:2.2.0-cuda12.1-cudnn8-devel"
TEMPLATE_DISK_SIZE=24  # Disk size in GB

# Define the destination folder on the remote machine
REMOTE_APP_DIR="wfs"

# Custom command to run after updating the code on the server
RESTART_SERVER_COMMAND="VALUE=\$(lsof -t -i:9090) && kill -9 \$VALUE && echo 'process id stopped:' \$VALUE && cd \"$REMOTE_APP_DIR\" && bash run.sh && echo 'process started'"

# Domain routines
DOMAIN="plavno.app"

FULL_SUBDOMAIN=$(clean_domain_name "$MACHINE_NAME.$DOMAIN")

# Command to run during initial setup of the machine
SETUP_COMMAND=$(cat <<EOF
mkdir -p "$REMOTE_APP_DIR" && \
sudo apt-get update && \
sudo apt-get install -y git-lfs && \
sudo apt-get install -y lsof && \
cd "$REMOTE_APP_DIR" && \
git clone --depth 1 --progress https://huggingface.co/Systran/faster-whisper-large-v3 && \
rm -rf faster-whisper-large-v3/.git
EOF
)

# Define directories and files to copy
CERTIFICATE_FILES=$(find certificates -maxdepth 1 -type f)
COPY_FOLDERS_COMMAND="$(echo whisper_live requirements translation_tools) $(find . -maxdepth 1 -type f)"

# Install dependencies and run project
INSTALL_COMMAND="cd \"$REMOTE_APP_DIR\" && bash setup.sh && bash run.sh"

# Destroy command
DESTROY_COMMAND="vastai destroy instance \$EXISTING_INSTANCE"
