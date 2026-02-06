#!/bin/bash

# Generate everytime container up
echo "Generating self-signed certificate..."
openssl req -x509 -newkey rsa:2048 -nodes -keyout /etc/ssl/private/priv.key -out /etc/ssl/certs/cert.pem -subj "/C=MY/ST=Shah Alam/L=i-City/O=RMS/OU=Technical/CN=localhost"

# supervisor handler
## if no value set to true
if [ -z "$APACHE2_SUPERVISOR_AUTOSTART" ]; then
  export APACHE2_SUPERVISOR_AUTOSTART=true
fi
## if no value set to true
if [ -z "$POSTFIX_SUPERVISOR_AUTOSTART" ]; then
  export POSTFIX_SUPERVISOR_AUTOSTART=true
fi

# Define paths
CLI_TARGET_PATH=$(php -i | grep conf | grep newrelic.ini | sed 's/,//g')

# Replace license key and app name
sed -i -e "s|REPLACE_WITH_REAL_KEY|$NEW_RELIC_LICENSE_KEY|g" \
       -e "s|PHP Application|$NEW_RELIC_APP_NAME|g" \
       "$CLI_TARGET_PATH"

# Enable newrelic if license key length is non-zero (not empty)
if [ -n "$NEW_RELIC_LICENSE_KEY" ]; then
  sed -i -e "s|^newrelic.enabled = false|newrelic.enabled = true|g" "$CLI_TARGET_PATH"
fi
# Replace daemon address if env var is set
if [ -n "$NEW_RELIC_DAEMON_ADDRESS" ]; then
  sed -i -e "s|^;newrelic\.daemon\.address = .*|newrelic.daemon.address = \"$NEW_RELIC_DAEMON_ADDRESS\"|g" "$CLI_TARGET_PATH"
fi


# Start Apache in the foreground (important for Docker container)
exec /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf
