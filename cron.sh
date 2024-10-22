#!/bin/bash

PORT=5000
SERVICE="codebreaker"  # Replace with the actual service name (e.g., "flask_app")

if ! ss -tulpn | grep -q ":$PORT "; then
    echo "$(date) - Port $PORT not in use, restarting $SERVICE" >> /var/log/check_port_5000.log
    sudo systemctl stop apache2
    sudo systemctl restart nginx
    sudo systemctl restart $SERVICE
else
    echo "$(date) - Port $PORT in use" >> /var/log/check_port_5000.log
fi
