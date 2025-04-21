provider "aws" {
  region = "us-east-1"
}

# Get the default VPC
data "aws_vpc" "default" {
  default = true
}

# Create Security Group
resource "aws_security_group" "savanna_sg" {
  name        = "savanna-app-sg-new"
  description = "Allow SSH and Django app traffic"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Django App Port"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "savanna-app-sg"
  }
}

# EC2 instance
resource "aws_instance" "savanna_server" {
  ami = "ami-0c1907b6d738188e5" # Ubuntu 22.04 LTS

  instance_type = "t2.micro"
  key_name      = var.key_name

  associate_public_ip_address = true

  vpc_security_group_ids = [aws_security_group.savanna_sg.id] # ✅ Attach SG here

  tags = {
    Name = "savanna-ec2"
  }

  connection {
    type        = "ssh"
    user        = "ubuntu"
    private_key = file(var.private_key_path)
    host        = self.public_ip
  }
}

# Output public IP
output "public_ip" {
  value = aws_instance.savanna_server.public_ip
}