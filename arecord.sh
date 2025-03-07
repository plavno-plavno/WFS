#!/bin/bash

# Extract ID and IP
ID=$(grep -o "C\.[0-9]*" /root/.vast_containerlabel | sed 's/C\.//')
IP=$(curl -s ifconfig.co)

# Log ID and IP for debugging
echo "Extracted ID: $ID"
echo "Detected IP: $IP"

# Function to create an A record in Cloudflare
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

# Function to set up Vast.ai machine label using vastai CLI
setup_vast_ai_label() {
    local label="c_${ID}"

    # Check if Vast.ai CLI is installed
    if ! command -v vastai &> /dev/null; then
        echo "Error: Vast.ai CLI (vastai) is not installed."
        return 1
    fi

    # Assign the label to the machine using the CLI
    response=$(vastai label instance "$ID" "$label" 2>&1)

    if [[ $? -eq 0 ]]; then
        echo "Successfully labeled Vast.ai instance $ID with label $label."
    else
        echo "Failed to label Vast.ai instance $ID."
        echo "Response: $response"
    fi
}

# Call the Cloudflare A record creation function
create_a_record "c${ID}" $IP

# Call the Vast.ai label setup function
setup_vast_ai_label
