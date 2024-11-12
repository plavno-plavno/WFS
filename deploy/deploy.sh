#!/bin/bash

# Load configuration from config.sh
source deploy/config.sh

generate_certificate() {
    local email=$1
    local domain=$2
    local cloudflare_credentials_path="deploy/cloudflare.ini"
    local certificates_dir="certificates"  # Update this path

    echo "Generating SSL certificate for $domain using Let's Encrypt with DNS challenge..."

    # Ensure the certificates directory exists
    mkdir -p "$certificates_dir"

    # Run Certbot with DNS-01 challenge using Cloudflare API and a deploy hook to copy the files
    sudo certbot certonly --dns-cloudflare \
        --dns-cloudflare-credentials "$cloudflare_credentials_path" \
        --agree-tos --no-eff-email \
        --email "$email" \
        -d "$domain" \
        --deploy-hook "sudo cp /etc/letsencrypt/live/$domain/* $certificates_dir/"

    if [ $? -eq 0 ]; then
        echo "SSL certificate generated and copied to $certificates_dir successfully for $domain."
    else
        echo "Failed to generate SSL certificate for $domain."
        exit 1
    fi
}

# Function to install Certbot on the host machine
install_certbot() {
    echo "Installing Certbot and Cloudflare DNS plugin on the host machine..."

    sudo apt-get update
    sudo apt-get install -y certbot python3-certbot-dns-cloudflare

    if [ $? -eq 0 ]; then
        echo "Certbot and DNS plugin installed successfully."
    else
        echo "Failed to install Certbot or DNS plugin."
        exit 1
    fi
}

# Function to create an A record for the given domain on Cloudflare
create_a_record() {
    local domain_name=$1
    local ip_address=$2

    # Check if required Cloudflare API credentials are set
    if [[ -z "$ZONE_ID" || -z "$CLOUDFLARE_API_KEY" ]]; then
        echo "Error: ZONE_ID and CLOUDFLARE_API_KEY must be set."
        return 1
    fi

    # Create the A record using Cloudflare API
    response=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $CLOUDFLARE_API_KEY" \
        -d '{
              "type": "A",
              "name": "'"$domain_name"'",
              "content": "'"$ip_address"'",
              "ttl": 3600,
              "proxied": false
            }')

    # Check if the response indicates a successful creation
    if echo "$response" | grep -q '"success":true'; then
        echo "A record created successfully for $domain_name with IP $ip_address."
    else
        echo "Failed to create A record for $domain_name."
        echo "Response: $response"
    fi
}

# Function to wait for an instance to be ready on Vast.ai with a timeout
wait_for_instance_ready() {
    local instance_id=$1
    local timeout=300  # Timeout in seconds
    local interval=10  # Interval in seconds
    local elapsed_time=0

    echo "Waiting for instance $instance_id to be ready..."

    while true; do
        # Check the instance status using vastai CLI
        status=$(vastai show instance "$instance_id" --raw | grep -o '"actual_status": "[^"]*' | sed 's/"actual_status": "//')
        if [ "$status" == "running" ]; then
            echo "Instance $instance_id is ready!"
            return 0
        fi

        # Check for timeout
        ((elapsed_time+=interval))
        if [ "$elapsed_time" -ge "$timeout" ]; then
            echo "Timeout reached. Instance $instance_id is not ready after $((timeout / 60)) minutes."
            echo "Destroying instance $instance_id..."

            # Attempt to destroy the instance if it didn't become ready in time
            vastai destroy instance "$instance_id"
            if [ $? -eq 0 ]; then
                echo "Instance $instance_id has been successfully destroyed."
            else
                echo "Failed to destroy instance $instance_id. Please check manually."
            fi
            return 1
        fi

        # Wait before the next status check
        echo "Instance status: $status. Waiting..."
        sleep $interval
    done
}

# Ensure the SSH key path is correct
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo "Error: SSH key not found at $SSH_KEY_PATH."
    echo "Please make sure your SSH key exists or set the correct path."
    echo "To generate a new SSH key pair, run the following command:"
    echo ""
    echo "    ssh-keygen -t rsa -b 4096 -C \"your_email@example.com\""
    echo ""
    echo "After running this command, follow the prompts to save the key as $SSH_KEY_PATH."
    echo "Then add this key to your SSH agent with:"
    echo ""
    echo "    eval \$(ssh-agent -s)"
    echo "    ssh-add $SSH_KEY_PATH"
    echo "Then add this key to your Vast.ai account."
    exit 1
fi

# Export the Vast.ai API key for use with the vastai CLI
export VAST_API_KEY="$VAST_API_KEY"

# Check if the vastai CLI is installed; if not, install it
if ! command -v vastai &> /dev/null; then
    echo "vastai CLI could not be found. Installing it using pip..."
    pip install --upgrade vastai
    if [ $? -ne 0 ]; then
        echo "Failed to install vastai CLI. Please check your Python and pip installation."
        exit 1
    fi
fi

# Step 1: Check if an existing instance with the desired machine name is running
echo "Checking for an existing instance with the machine label: $MACHINE_NAME..."
EXISTING_INSTANCE=$(vastai show instances | grep "$MACHINE_NAME" | awk '{print $1}')

if [ -n "$EXISTING_INSTANCE" ]; then
    echo "Found an existing instance with ID: $EXISTING_INSTANCE"

    # Retrieve SSH URL of the existing instance
    EXISTING_INSTANCE_IP=$(vastai ssh-url "$EXISTING_INSTANCE" --api-key "$VAST_API_KEY")

    if [ -z "$EXISTING_INSTANCE_IP" ]; then
        echo "Failed to fetch the SSH details of the existing instance. Exiting."
        exit 1
    fi

    echo "Existing instance SSH address: $EXISTING_INSTANCE_IP"

    # Parse host and port from SSH URL
    RHOST=$(echo "$EXISTING_INSTANCE_IP" | sed -E 's#ssh://([^:]+):[0-9]+#\1#')
    RPORT=$(echo "$EXISTING_INSTANCE_IP" | sed -E 's#ssh://[^:]+:([0-9]+)#\1#')

    # Step 2: Update code on the existing instance using rsync
    echo "Updating code on the existing instance using rsync..."
    rsync -avz -e "ssh -i $SSH_KEY_PATH -p $RPORT -o StrictHostKeyChecking=no" $COPY_FOLDERS_COMMAND "$RHOST:$REMOTE_APP_DIR/"
    sudo rsync -avz -e "ssh -i $SSH_KEY_PATH -p $RPORT -o StrictHostKeyChecking=no" $CERTIFICATE_FILES "$RHOST:$REMOTE_APP_DIR/certificates/"
    sudo rsync -avz -e "ssh -i $SSH_KEY_PATH -p $RPORT -o StrictHostKeyChecking=no" $MADLAD_FILES "$RHOST:$REMOTE_APP_DIR/madlad400-3b/"

    # Step 3: Restart the server on the existing instance
    echo "Running command to restart the server on the existing instance..."
    ssh -i "$SSH_KEY_PATH" $EXISTING_INSTANCE_IP << EOF
        $RESTART_SERVER_COMMAND
EOF

    echo "Server restarted successfully on the existing instance."
    exit 0
fi

# Step 4: No existing instance found; create a new one
echo "No existing instance found. Creating a new instance on Vast.ai..."

# Get a list of available machines and select one
echo "Fetching a list of available machines with GPU type: $DESIRED_GPU_TYPE..."
vastai search offers "gpu_name==$DESIRED_GPU_TYPE reliability > 0.99 num_gpus=$DESIRED_GPU_AMOUNT" -o 'dlperf_usd-' > available_machines.txt
MACHINE_ID=$(awk 'NR==2 {print $1}' available_machines.txt)

if [ -z "$MACHINE_ID" ]; then
    echo "No suitable machine found with GPU type: $DESIRED_GPU_TYPE. Exiting."
    exit 1
fi

echo "Selected machine ID: $MACHINE_ID"

# Step 5: Create and start an instance with the selected machine ID
INSTANCE_ID=$(vastai create instance $MACHINE_ID --image "$TEMPLATE_IMAGE" --disk $TEMPLATE_DISK_SIZE --ssh --env '-p 22:22 -p 8080:8080 -p 8081:8081 -p 9090:9090' --label "$MACHINE_NAME" | grep -oP "'new_contract': \K\d+")
echo "Instance ID created: $INSTANCE_ID"
vastai start instance $INSTANCE_ID

# Step 6: Wait for the instance to be ready
if wait_for_instance_ready "$INSTANCE_ID"; then
    echo "Instance is ready. Proceeding with the next steps..."
else
    exit 1
fi

# Step 7: Fetch SSH details
INSTANCE_IP=$(vastai ssh-url "$INSTANCE_ID" --api-key "$VAST_API_KEY")
echo $INSTANCE_IP

RHOST=$(echo "$INSTANCE_IP" | sed -E 's#ssh://[^@]+@([0-9.]+):[0-9]+#\1#')
RPORT=$(echo "$INSTANCE_IP" | sed -E 's#ssh://[^@]+@[0-9.]+:([0-9]+)#\1#')

echo $RHOST
echo $RPORT

create_a_record "$FULL_SUBDOMAIN" "$RHOST"
# install_certbot
# generate_certificate "$EMAIL" "$FULL_SUBDOMAIN"

# Step 8: SSH into the instance and set up the environment
ssh -i "$SSH_KEY_PATH" $INSTANCE_IP -o StrictHostKeyChecking=no << EOF
    $SETUP_COMMAND
EOF


sleep 5
echo 'SENDING CERTIFICATE_FILES'

# Step 0: Ensure the certificates folder exists on the remote machine
ssh -i "$SSH_KEY_PATH" -p "$RPORT" -o StrictHostKeyChecking=no "$RHOST" "mkdir -p $REMOTE_APP_DIR/certificates"
sleep 5
# Step 1: Deliver certificates files to the remote app folder's certificates subdirectory
sudo rsync -avz -e "ssh -i $SSH_KEY_PATH -p $RPORT -o StrictHostKeyChecking=no" "$CERTIFICATE_FILES" "$RHOST:$REMOTE_APP_DIR/certificates/"
sleep 10

echo 'SENDING COPY_FOLDERS_COMMAND'
# Step 2: Deliver everything else to the remote app folder
sudo rsync -avz -e "ssh -i $SSH_KEY_PATH -p $RPORT -o StrictHostKeyChecking=no" $COPY_FOLDERS_COMMAND "$RHOST:$REMOTE_APP_DIR/"


echo 'SENDING MADLAD_FILES'
sudo rsync -avz -e "ssh -i $SSH_KEY_PATH -p $RPORT -o StrictHostKeyChecking=no" $MADLAD_FILES "$RHOST:$REMOTE_APP_DIR/madlad400-3b/"

sleep 5
echo 'run INSTALL_COMMAND'
# Run the installation command on the remote server
ssh -i "$SSH_KEY_PATH" $INSTANCE_IP -o StrictHostKeyChecking=no << EOF
    source ~/.bashrc
    $INSTALL_COMMAND
EOF

echo "You can now access the instance via: ssh -i $SSH_KEY_PATH $INSTANCE_IP"
echo "Use subdomain to access service $FULL_SUBDOMAIN"