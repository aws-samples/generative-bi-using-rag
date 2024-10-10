#!/bin/bash

# 执行第一个脚本
echo "Running environment_preparation.sh..."
bash environment_preparation.sh

# 检查上一个脚本是否成功执行
if [ $? -eq 0 ]; then
    echo "environment_preparation.sh executed successfully."
else
    echo "environment_preparation.sh failed. Exiting..."
    exit 1
fi

# 获取本地IPv4地址
LOCAL_IP=$(hostname -I | awk '{print $1}')

# 获取公网IP地址
PUBLIC_IP=$(curl -s ifconfig.me)

# 获取当前目录
CURRENT_DIR=$(pwd)

# 查找当前目录下的.env文件
ENV_FILE=$(find "$CURRENT_DIR" -name ".env")

if [ -z "$ENV_FILE" ]; then
  echo "未找到.env文件"
  exit 1
fi

# 替换.env文件中的DYNAMODB_ENDPOINT变量
sed -i "s|^DYNAMODB_ENDPOINT=.*|DYNAMODB_ENDPOINT=http://$LOCAL_IP:8001|" "$ENV_FILE"

echo "DYNAMODB_ENDPOINT已更新为本地IPv4地址: $LOCAL_IP"



# 获取公网IP地址
PUBLIC_IP=$(curl -s ifconfig.me)

# 获取当前目录
CURRENT_DIR=$(pwd)

# 查找report-front-end目录下的.env文件
ENV_FILE=$(find "$CURRENT_DIR/../report-front-end" -name ".env")

if [ -z "$ENV_FILE" ]; then
  echo "未找到report-front-end目录下的.env文件"
  exit 1
fi

# 替换.env文件中的VITE_BACKEND_URL和VITE_WEBSOCKET_URL变量
sed -i "s|^VITE_BACKEND_URL=http://.*:8000|VITE_BACKEND_URL=http://$PUBLIC_IP:8000|" "$ENV_FILE"
sed -i "s|^VITE_WEBSOCKET_URL=ws://.*:8000/qa/ws|VITE_WEBSOCKET_URL=ws://$PUBLIC_IP:8000/qa/ws|" "$ENV_FILE"

echo "VITE_BACKEND_URL和VITE_WEBSOCKET_URL已更新为公网IP地址: $PUBLIC_IP"




# 执行第二个脚本
echo "Running docker-compose-build.sh..."
bash docker-compose-build.sh

# 检查上一个脚本是否成功执行
if [ $? -eq 0 ]; then
    echo "docker-compose-build.sh executed successfully."
else
    echo "docker-compose-build.sh failed. Exiting..."
    exit 1
fi

# 执行第三个脚本
echo "Running import_sql_data.sh..."
bash import_sql_data.sh

sleep 20

# 检查上一个脚本是否成功执行
if [ $? -eq 0 ]; then
    echo "import_sql_data.sh executed successfully."
else
    echo "import_sql_data.sh failed. Exiting..."
    exit 1
fi

echo "All scripts executed successfully."