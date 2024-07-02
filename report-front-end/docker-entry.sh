#!/bin/sh

# Read variable names from the .env file
env_file="/.env"
vars="VITE_COGNITO_REGION
VITE_COGNITO_USER_POOL_ID
VITE_COGNITO_USER_POOL_WEB_CLIENT_ID
VITE_BACKEND_URL
VITE_WEBSOCKET_URL"

# Iterate through .js files in /usr/share/nginx/html and replace variables
find "/usr/share/nginx/html" -type f -name "*.js" | while read file; do
    for var in $vars; do
        placeholder="PLACEHOLDER_$var"
        value=$(printenv $var)
        echo "Replacing $placeholder with $value"
        sed -i "s/$placeholder/$value/g" $file
    done
done

exec "$@"