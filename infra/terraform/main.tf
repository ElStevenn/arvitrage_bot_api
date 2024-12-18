provider "aws" {
  region = "eu-south-2"
}

resource "aws_key_pair" "instance_key" {
  key_name   = "developer_key"
  public_key = file("../../src/security/instance_key2.pem.pub")
}

resource "aws_eip" "main_api_eip" {
  domain = "vpc"
  tags = {
    Name = "Arvitrage API"
  }
}

resource "aws_eip_association" "main_api_eip_assoc" {
  instance_id   = aws_instance.historical_funding_rate.id
  allocation_id = aws_eip.main_api_eip.id
}

data "aws_security_group" "paus-security-group" {
  name = "paus-security-group"
  id   = "sg-0ceebb5821128f97d"
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"]

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "historical_funding_rate" {
  ami                    = var.ami_id
  instance_type          = "t3.medium"
  key_name               = aws_key_pair.instance_key.key_name
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [data.aws_security_group.paus-security-group.id]

  tags = {
    Name = "Arvitrage API"
    Type = "Pau's architecture"
  }

  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    delete_on_termination = true
  }

  lifecycle {
    ignore_changes = [ami] # Prevent Terraform from recreating due to AMI drift
  }

  provisioner "local-exec" {
    command = <<EOT
      cd .. &&
      cd .. &&
      git add . &&
      git commit -m "${var.commit_message}" &&
      git push -u origin main
    EOT
  }

  provisioner "file" {
    source      = "/home/mrpau/Desktop/Secret_Project/other_layers/Arvitrage_bot_API/src/scripts"
    destination = "/home/ubuntu/scripts"

    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("../../src/security/instance_key2.pem")
      host        = self.public_ip
    }
  }

  provisioner "remote-exec" {
    inline = [
      "chmod +x /home/ubuntu/scripts/CI/*",
      "bash /home/ubuntu/scripts/source.sh"
    ]

    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("../../src/security/instance_key2.pem")
      host        = self.public_ip
    }
  }

  provisioner "file" {
    source      = "/home/mrpau/Desktop/Secret_Project/other_layers/Arvitrage_bot_API/src/.env"
    destination = "/home/ubuntu/.env"

    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("../../src/security/instance_key2.pem")
      host        = self.public_ip
    }
  }
}

resource "null_resource" "post_eip_setup" {
  depends_on = [aws_eip_association.main_api_eip_assoc]

  provisioner "remote-exec" {
    inline = [
      "chmod +x /home/ubuntu/scripts/CI/build.sh",
      "bash /home/ubuntu/scripts/CI/build.sh"
    ]

    connection {
      type        = "ssh"
      user        = "ubuntu"
      private_key = file("../../src/security/instance_key2.pem")
      host        = aws_eip.main_api_eip.public_ip
    }
  }
}

output "elastic_ip" {
  value       = aws_eip.main_api_eip.public_ip
  description = "The Elastic IP address associated with the EC2 instance."
}
