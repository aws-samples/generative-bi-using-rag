# Sleep 60 seconds to avoid yum failures
# Ref: https://repost.aws/questions/QUgNz4VGCFSC2TYekM-6GiDQ/dnf-yum-both-fails-while-being-executed-on-instance-bootstrap-on-amazon-linux-2023
sleep 60

sudo su - ec2-user

# Install components
sudo yum install docker python3-pip git -y && sudo pip3 install -U awscli

# Remove python3-requests to avoid conflict with docker-compose
# Ref: https://stackoverflow.com/questions/76443104/error-cannot-uninstall-requests-2-25-1-record-file-not-found-hint-the-packag
sudo yum -y remove python3-requests

sudo pip3 install docker-compose

# Fix docker python wrapper 7.0 SSL version issue  
sudo pip3 install docker==6.1.3

# Configure components
sudo systemctl enable docker 
sudo systemctl start docker 
echo "finishing starting docker"
sudo usermod -aG docker $USER
echo "finishing adding user to docker group"

# Exit the terminal
exit