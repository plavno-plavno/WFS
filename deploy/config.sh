# config.sh

# Set your Vast.ai API key
VAST_API_KEY="bf299128b308697749900f6b3b6c9f758b35b9a5f4a33c1c71b5fad44d237231"

# Path to your SSH private key
SSH_KEY_PATH="$HOME/.ssh/rsa_vast"

# Define the desired GPU type and amount
DESIRED_GPU_TYPE="RTX_4070"  # e.g., "RTX 3090", "Tesla V100", "A100"
DESIRED_GPU_AMOUNT=1

# Define the template for instance creation
TEMPLATE_IMAGE="pytorch/pytorch:2.2.0-cuda12.1-cudnn8-devel"
TEMPLATE_DISK_SIZE=24  # Disk size in GB

# Define the machine name to check for or assign to new instances
MACHINE_NAME="Dudkevich_for_Kugleyko_front"

REMOTE_APP_DIR="wfs"

# Custom command to run after updating the code on the server
RESTART_SERVER_COMMAND="VALUE=\$(lsof -t -i:9090)  && kill -9 \$VALUE && echo 'process id stopped:' \$VALUE &&  cd $REMOTE_APP_DIR && bash run.sh && echo 'process started'"

# Define the destination folder on the remote machine
REMOTE_APP_DIR="wfs"

# Command to run during initial setup of the machine
SETUP_COMMAND=$(cat <<EOF
mkdir -p "$REMOTE_APP_DIR" && \
sudo apt-get update && \
sudo apt-get install -y git-lfs && \
sudo apt-get install lsof && \
cd "$REMOTE_APP_DIR" && \
git clone --progress https://huggingface.co/Systran/faster-whisper-large-v3
EOF
)

# Specify folders and files to copy
COPY_FOLDERS_COMMAND="whisper_live requirements translation_tools $(find . -maxdepth 1 -type f)"

#install dependencies and run project
INSTALL_COMMAND="cd $REMOTE_APP_DIR && bash setup.sh && bash run.sh"

DESTROY_COMMAND="vastai destroy instance \$EXISTING_INSTANCE"