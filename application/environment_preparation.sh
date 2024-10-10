#!/bin/bash

# 对于组件
echo "Installing Docker, Python3-pip, and Git..."
sudo yum install docker python3-pip git -y
echo "Docker, Python3-pip, and Git installed successfully."

# 安装docker-compose
echo "Installing Docker Compose..."
sudo pip3 install --ignore-installed docker-compose
echo "Docker Compose installed successfully."

# 修复docker的python包装器7.0 SSL版本问题
echo "Fixing Docker Python wrapper SSL version issue..."
pip3 install docker==6.1.3
echo "Docker Python wrapper SSL version issue fixed successfully."

# 修复requests版本升级导致的问题
echo "Fixing requests version upgrade issue..."
pip3 install requests==2.31.0
echo "Requests version upgrade issue fixed successfully."

# 配置组件
echo "Configuring Docker service..."
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER
echo "Docker service configured successfully."

# 使用子shell执行newgrp docker及后续命令
(
    newgrp docker << EOF
    # 刷新当前用户的组成员身份
    echo "Refreshing current user's group membership..."
    echo "Current user's group membership refreshed successfully."

    # 配置OpenSearch的服务器参数
    echo "Configuring OpenSearch server parameters..."
    sudo sh -c "echo 'vm.max_map_count=262144' > /etc/sysctl.conf" && sudo sysctl -p
    echo "OpenSearch server parameters configured successfully."
EOF
)

echo "Script execution completed."