# Log in as user ec2-user

# Configure OpenSearch server parameters
sudo sh -c "echo 'vm.max_map_count=262144' > /etc/sysctl.conf" && sudo sysctl -p

# Clone the code
# git clone https://github.com/aws-samples/generative-bi-using-rag.git
wget https://aws-genbi-guidance-asset.s3.us-west-2.amazonaws.com/asset/code/genbi-guidance-asset.zip
unzip genbi-guidance-asset.zip

# Config the Environment Variable in .env file, modify AWS_DEFAULT_REGION to the region same as the EC2 instance.
cd genbi-guidance-asset/application && cp .env.cntemplate .env 

file_path=".env"
ec2_region=`curl -s http://169.254.169.254/latest/meta-data/placement/region`
sed -i "s|AOS_AWS_REGION=ap-northeast-1|AOS_AWS_REGION=$ec2_region|g" $file_path
sed -i "s|RDS_REGION_NAME=ap-northeast-1|RDS_REGION_NAME=$ec2_region|g" $file_path
sed -i "s|AWS_DEFAULT_REGION=ap-northeast-1|AWS_DEFAULT_REGION=$ec2_region|g" $file_path
sed -i "s|DYNAMODB_AWS_REGION=us-west-2|AWS_DEFAULT_REGION=$ec2_region|g" $file_path


# # Build docker images locally
# docker-compose build

# # Start all services
# docker-compose up -d

# # Wait 3 minutes for MySQL and OpenSearch to initialize
# sleep 180

# cd initial_data && wget https://github.com/fengxu1211/generative-bi-using-rag/raw/demo_data/application/initial_data/init_mysql_db.sql.zip

# unzip init_mysql_db.sql.zip && cd ..

# docker exec nlq-mysql sh -c "mysql -u root -ppassword -D llm  < /opt/data/init_mysql_db.sql" 

# docker exec nlq-webserver python opensearch_deploy.py

# echo "All services are started successfully. Please access the application at http://<ec2-public-ip>"