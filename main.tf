provider "aws" {
    region = "eu-south-2"
}

resource "aws_security_group" "545009827213-funding-rate" {
  name        = "545009827213-funding-rate"
  description = "Security group mainly used in MongoDB - HTTP applications"
  vpc_id      = var.main.id

  tags = {
    Name = "allow_mongo"
  }

  # Ingress = inbound rules | egress = outbound rules 

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [ "0.0.0.0/0" ]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [ "0.0.0.0/0" ]
  }

  ingress {
    from_port   = 8000
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = [ "0.0.0.0/0" ]
  }

  ingress {
    from_port   = 27017
    to_port     = 27017
    protocol    = "tcp"
    cidr_blocks = [ "0.0.0.0/0" ]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [ "0.0.0.0/0" ]
  }

}

resource "aws_instance" "historical_funding_rate" {
  ami                    = "ami-08a361410fcb2f861"
  instance_type          = "t3.medium"
  key_name               = "instance_key"
  subnet_id              = var.main.subnet_id
  vpc_security_group_ids = [aws_security_group.545009827213-funding-rate]

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
    delete_on_termination = true
  }


  tags = {
    Name = "CryptoProject"
  }

  provisioner "remote-exec" {
    inline = [ 
      "sudo apt update -y",
      "sudo timedatectl set-timezone Europe/Madrid",

      # Install Docker & Dependences
      "sudo apt-get install ca-certificates curl",
      "sudo install -m 0755 -d /etc/apt/keyrings",
      "sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc",
      "echo \"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo \\\"$VERSION_CODENAME\\\") stable\" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null",

      "sudo apt-get update",

      "sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin",

      # Install Jenkins
      "sudo apt install -y openjdk-11-jdk wget",
      "wget -q -O - https://pkg.jenkins.io/debian-stable/jenkins.io.key | sudo apt-key add -",
      "sudo sh -c 'echo deb http://pkg.jenkins.io/debian-stable binary/ > /etc/apt/sources.list.d/jenkins.list'",
      "sudo apt update -y",
      "sudo apt install -y jenkins",
      "sudo systemctl start jenkins",
      "sudo systemctl enable jenkins",

      # Run setup server
      "chmod +x setup_server.sh",
      "./setup_server.sh",
      
      # Call CI Pipeline
      "docker build -t funding_rate ."



     ]
  }
}
