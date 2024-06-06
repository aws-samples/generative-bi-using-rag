#!/bin/bash

# 提示用户输入容器名称
# read -p "请输入要停止和删除的容器名称: " container_name

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

    docker-compose build

    docker-compose up -d

    echo "容器 $container_name 已重新启动."
else
    echo "没有找到名称为 $container_name 的容器."

    docker-compose build

    docker-compose up -d

    echo "容器 $container_name 已重新启动."
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

    docker-compose build

    docker-compose up -d

    echo "容器 $container_name 已重新启动."
else
    echo "没有找到名称为 $container_name 的容器."

    docker-compose build

    docker-compose up -d

    echo "容器 $container_name 已重新启动."
fi

docker images -q --filter "dangling=true" | xargs -r docker rmi