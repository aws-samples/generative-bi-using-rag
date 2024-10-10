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

sleep 20s
echo "database Start ..."

# 执行第三个脚本
echo "Running import_sql_data.sh..."
bash import_sql_data.sh

# 检查上一个脚本是否成功执行
if [ $? -eq 0 ]; then
    echo "import_sql_data.sh executed successfully."
else
    echo "import_sql_data.sh failed. Exiting..."
    exit 1
fi

echo "All scripts executed successfully."