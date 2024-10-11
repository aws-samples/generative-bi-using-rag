#!/bin/bash

# 使用 newgrp docker 切换到 docker 组
newgrp docker << EOF

# 定义一个函数来处理容器的停止和删除
stop_and_remove_container() {
    local container_name=$1
    local container_id=$(docker ps -aq --filter="name=$container_name")

    if [ -n "$container_id" ]; then
        echo "正在停止容器 $container_name..."
        docker stop $container_id

        echo "正在删除容器 $container_name..."
        docker rm $container_id

        echo "容器 $container_name 已成功停止和删除."
    else
        echo "没有找到名称为 $container_name 的容器."
    fi
}
# 处理每个容器
stop_and_remove_container "nlq-webserver"
stop_and_remove_container "nlq-api"
stop_and_remove_container "react-front-end"

# 构建和启动容器
docker-compose build
docker-compose up -d

# 删除未使用的镜像
docker images -q --filter "dangling=true" | xargs -r docker rmi

EOF