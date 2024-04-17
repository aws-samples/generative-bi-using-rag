# Log in as user ec2-user

# Configure OpenSearch server parameters
sudo sh -c "echo 'vm.max_map_count=262144' > /etc/sysctl.conf" && sudo sysctl -p

# Clone the code
git clone https://github.com/aws-samples/generative-bi-using-rag.git

# Config the Environment Variable in .env file, modify AWS_DEFAULT_REGION to the region same as the EC2 instance.
cd generative-bi-using-rag/application && cp .env.template .env 

# Build docker images locally
docker-compose build

# Start all services
docker-compose up -d

# Wait 3 minutes for MySQL and OpenSearch to initialize
sleep 180

cd initial_data && wget https://github.com/fengxu1211/generative-bi-using-rag/raw/demo_data/application/initial_data/init_mysql_db.sql.zip

unzip init_mysql_db.sql.zip && cd ..

docker exec nlq-mysql sh -c "mysql -u root -ppassword -D llm  < /opt/data/init_mysql_db.sql" 

docker exec nlq-webserver python opensearch_deploy.py

echo "All services are started successfully. Please access the application at http://<ec2-public-ip>"