#!/bin/sh

# Read variable names from the .env file
env_file="/.env"
vars="VITE_COGNITO_REGION
VITE_LOGIN_TYPE
VITE_COGNITO_USER_POOL_WEB_CLIENT_ID
VITE_COGNITO_USER_POOL_ID
VITE_BACKEND_URL
VITE_WEBSOCKET_URL"

# Iterate through .js files in /usr/share/nginx/html and replace variables
find "/usr/share/nginx/html" -type f -name "*.js" | while read -r file; do
    for var in $vars; do
        placeholder="PLACEHOLDER_$var"
        value=$(eval "echo \$$var")
        
        # Escape special characters in the value for use in sed
        escaped_value=$(printf '%s\n' "$value" | sed -e 's/[\/&]/\\&/g')

        echo "Replacing $placeholder with $escaped_value in $file"
        sed -i "s/$placeholder/$escaped_value/g" "$file"
    done
done

exec "$@"
