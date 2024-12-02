#!/bin/bash
sudo apt update -y
sudo timedatectl set-timezone Europe/Madrid
sudo apt install -y unzip curl jq

# Install jq if not already installed
if ! command -v jq &> /dev/null; then
  sudo apt install jq -y
fi

# Install Docker & Dependencies
sudo apt-get install -y \
  ca-certificates \
  curl \
  gnupg \
  lsb-release

# Install AWS CLI
if ! command -v aws &> /dev/null; then
  echo "AWS CLI not found. Installing..."
  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
  unzip awscliv2.zip
  sudo ./aws/install
  if ! command -v aws &> /dev/null; then
    echo "AWS CLI installation failed."
    exit 1
  fi
fi
echo "AWS CLI version: $(aws --version)"

# Check AWS CLI region
REGION=${AWS_REGION:-"us-east-1"}
export AWS_REGION=$REGION
echo "AWS CLI Region: $AWS_REGION"

# Retrieve AWS parameters
ACCESS_KEY=$(aws ssm get-parameter --name "/myapp/aws_access_key" --with-decryption --query "Parameter.Value" --output text 2>/dev/null)
SECRET_KEY=$(aws ssm get-parameter --name "/myapp/aws_secret_key" --with-decryption --query "Parameter.Value" --output text 2>/dev/null))

if [ -z "$ACCESS_KEY" ] || [ -z "$SECRET_KEY" ]; then
  echo "Failed to retrieve parameters. Check SSM Parameter Store and IAM role permissions."
  exit 1
fi

# Source the profile script to apply changes
source /etc/profile.d/aws_env.sh

sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Install Jenkins
sudo apt install -y openjdk-11-jdk wget
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io.key | sudo tee \
  /usr/share/keyrings/jenkins-keyring.asc > /dev/null

echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null

sudo apt update -y
sudo apt install -y jenkins
sudo systemctl start jenkins
sudo systemctl enable jenkins

# Run setup server script
chmod +x /home/ubuntu/api_funding_rate/scripts/*
sudo ./home/ubuntu/api_funding_rate/scripts/setup_server.sh


