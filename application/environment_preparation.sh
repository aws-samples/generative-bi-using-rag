# 对于组件

sudo yum install docker python3-pip git -y

# 安装docker-compose

sudo pip3 install --ignore-installed docker-compose

# 修复docker的python包装器7.0 SSL版本问题

pip3 install docker==6.1.3

# 修复requests版本升级导致的问题

pip3 install requests==2.31.0

# 配置组件
sudo systemctl enable docker

sudo systemctl start docker

sudo usermod -aG docker $USER

# 刷新当前用户的组成员身份

newgrp docker

# 配置OpenSearch的服务器参数
sudo sh -c "echo 'vm.max_map_count=262144' > /etc/sysctl.conf" && sudo sysctl -p


