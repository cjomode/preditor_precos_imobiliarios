provider "aws" {
  region = "us-east-1"
}

resource "aws_security_group" "streamlit_sg" {
  name        = "streamlit_sg"
  description = "Libera porta 8501 para o app Streamlit"

  ingress {
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
