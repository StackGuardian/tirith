provider "aws" {
  region = "us-west-2"  # Change this to your desired AWS region
}

resource "aws_security_group" "elb_sg" {
  name        = "elb-sg"
  description = "Security Group for ELB"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]  # Allow all incoming HTTP traffic. Modify as needed.
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]  # Allow all outgoing traffic. Modify as needed.
  }
}

resource "aws_elb" "example" {
  name               = "example-elb"
  availability_zones = ["us-west-2a", "us-west-2b"]  # Change these based on your region and requirements

  listener {
    instance_port     = 80
    instance_protocol = "http"
    lb_port           = 80
    lb_protocol       = "http"
  }

  security_groups = [aws_security_group.elb_sg.id]

  # Optionally add health checks, instances, etc.
}

resource "aws_elb" "something" {
  name               = "something-elb"
  availability_zones = ["us-west-2a", "us-west-2b"]  # Change these based on your region and requirements

  listener {
    instance_port     = 80
    instance_protocol = "http"
    lb_port           = 80
    lb_protocol       = "http"
  }

  security_groups = []

  # Optionally add health checks, instances, etc.
}
