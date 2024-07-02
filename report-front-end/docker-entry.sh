#!/bin/sh

echo "Injecting env vars into Vite's static files"
# replacing Vite's static env vars with injected one
vars=$(printenv | grep '^VITE_' | awk -F= '{print $1}')
find "/usr/share/nginx/html" -type f -name "*.js" | while read file; do
    for var in $vars; do
        echo "Replacing $var in $file"
        sed -i "s/\($var:\"\)[^\"]*\"/\1$(printenv "$var")\"/g" $file
    done
done

# Replace region, userPoolId, and userPoolWebClientId with VITE_COGNITO_REGION, VITE_COGNITO_USER_POOL_ID, and VITE_COGNITO_USER_POOL_WEB_CLIENT_ID values
find "/usr/share/nginx/html" -type f -name "*.js" | while read file; do
    echo "Replacing Cognito values in $file"
    sed -i 's/{region:"[^"]*",userPoolId:"[^"]*",userPoolWebClientId:"[^"]*"}\?/{region:"'"$VITE_COGNITO_REGION"'",userPoolId:"'"$VITE_COGNITO_USER_POOL_ID"'",userPoolWebClientId:"'"$VITE_COGNITO_USER_POOL_WEB_CLIENT_ID"'"}'/g "$file"
done

exec "$@"