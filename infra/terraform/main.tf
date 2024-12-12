provider "aws" {
  region = "eu-south-2"
}

resource "aws_key_pair" "instance_key" {
  key_name  = "developer_key"
  public_key = file("../../src/security/instance_key2.pem.pub")
}

# Security Group
resource "aws_security_group" "funding_rate" {
  name        = "funding_rate_sg"
  description = "Security group mainly used in MongoDB - HTTP applications"
  vpc_id      = var.vpc_id

  tags = {
    Name = "allow_mongo"
  }

  # Ingress Rules (Inbound)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] 
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Restrict MongoDB Port Access
  ingress {
    from_port   = 27017
    to_port     = 27017
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  
  }

  # Egress Rules (Outbound)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# IAM Role definition for ssm full acces
resource "aws_iam_role" "ssm_role" {
  name = "ssm_full_access_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "ec2.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ssm_full_access" {
  role       = aws_iam_role.ssm_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMFullAccess"
}

resource "aws_iam_instance_profile" "cli_permissions" {
  name = "cli_permissions"
  role = aws_iam_role.ssm_role.name
}


# Data Source for AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]  # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# EC2 Instance
resource "aws_instance" "historical_funding_rate" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = "t3.medium"
  key_name               = aws_key_pair.instance_key.key_name
  subnet_id              = var.subnet_id
  vpc_security_group_ids = ["sg-0ceebb5821128f97d"]

  iam_instance_profile   = aws_iam_instance_profile.cli_permissions.name

  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    delete_on_termination = true
  }

  tags = {
    Name = "CryptoProject"
  }

  provisioner "remote-exec" {
    inline = [
      "mkdir -p /home/ubuntu/api_funding_rate"
    ]

    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("../../src/security/instance_key2.pem")
      host        = self.public_ip
    }
  }

  provisioner "local-exec" {
    command = "tar -czf /tmp/historical_funding_rate_api.tar.gz -C /home/mrpau/Desktop/Secret_Project historical_funding_rate_api"
  }

  provisioner "file" {
    source      = "/tmp/historical_funding_rate_api.tar.gz"
    destination = "/home/ubuntu/historical_funding_rate_api.tar.gz"

    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("../../src/security/instance_key2.pem")
      host        = self.public_ip
    }
  }

  provisioner "remote-exec" {
    inline = [
      "sudo su",
      "tar -xzf /home/ubuntu/historical_funding_rate_api.tar.gz -C /home/ubuntu/",
      "rm /home/ubuntu/historical_funding_rate_api.tar.gz", # Cleanup archive
      "chmod +x /home/ubuntu/historical_funding_rate_api/scripts/*",
      "/home/ubuntu/historical_funding_rate_api/scripts/user_data.sh",
    ]

    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("../../src/security/instance_key2.pem")
      host        = self.public_ip
    }
  }

}