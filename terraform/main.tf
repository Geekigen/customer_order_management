terraform {
  backend "s3" {
    bucket         = "savannas3"
    key            = "terraform.tfstate"
    region         = "ap-southeast-1"
    dynamodb_table = "terraform-locks"
  }
}

# Resource definition for the existing DynamoDB table
resource "aws_dynamodb_table" "terraform_locks" {
  name         = "terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"  # This must be LockID for Terraform state locking

  attribute {
    name = "LockID"
    type = "S"  # String type
  }
}

# Your other resources (provider, vpc, security group, ec2, etc.) remain unchanged
provider "aws" {
  region = "ap-southeast-1"
}

# Get the default VPC
data "aws_vpc" "default" {
  default = true
}

# Create Security Group
resource "aws_security_group" "savanna_sg" {
  name_prefix = "savanna-app-sg-"
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
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
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

  # This prevents recreation of the security group when only tags change
  lifecycle {
    create_before_destroy = true
  }
}

# EC2 instance
resource "aws_instance" "savanna_server" {
  ami = "ami-01938df366ac2d954" # Ubuntu 22.04 LTS

  instance_type = "t2.micro"
  key_name      = var.key_name

  associate_public_ip_address = true

  vpc_security_group_ids = [aws_security_group.savanna_sg.id]

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