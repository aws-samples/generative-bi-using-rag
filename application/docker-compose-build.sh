#!/bin/bash

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



# 查找与输入名称匹配的容器
container_id=$(docker ps -aq --filter="name=nlq-webserver")

# 如果找到匹配的容器
if [ -n "$container_id" ]; then
    # 停止容器
    echo "正在停止容器 $container_name..."
    docker stop $container_id

    # 删除容器
    echo "正在删除容器 $container_name..."
    docker rm $container_id

    echo "容器 $container_name 已成功停止和删除."

    echo "容器 $container_name 已重新启动."
else
    echo "没有找到名称为 $container_name 的容器."
fi

container_id=$(docker ps -aq --filter="name=nlq-api")

# 如果找到匹配的容器
if [ -n "$container_id" ]; then
    # 停止容器
    echo "正在停止容器 $container_name..."
    docker stop $container_id

    # 删除容器
    echo "正在删除容器 $container_name..."
    docker rm $container_id

    echo "容器 $container_name 已成功停止和删除."

    echo "容器 $container_name 已重新启动."
else
    echo "没有找到名称为 $container_name 的容器."
fi

container_id=$(docker ps -aq --filter="name=react-front-end")

# 如果找到匹配的容器
if [ -n "$container_id" ]; then
    # 停止容器
    echo "正在停止容器 $container_name..."
    docker stop $container_id

    # 删除容器
    echo "正在删除容器 $container_name..."
    docker rm $container_id

    echo "容器 $container_name 已成功停止和删除."

    echo "容器 $container_name 已重新启动."
else
    echo "没有找到名称为 $container_name 的容器."
fi


docker-compose build

docker-compose up -d

docker images -q --filter "dangling=true" | xargs -r docker rmi