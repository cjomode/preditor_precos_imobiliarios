provider "aws" {
  region = "us-east-1"
}

resource "aws_key_pair" "deployer" {
  key_name   = "minha-chave"
  public_key = file("${path.module}/minha-chave.pub")

  # substitui pelo caminho da tua chave pública
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
resource "aws_instance" "streamlit_instance" {
  ami                         = "ami-0c55b159cbfafe1f0"  # AMI Ubuntu 22.04 na us-east-1 (podemos ajustar depois)
  instance_type               = var.instance_type
  key_name                    = var.key_name
  vpc_security_group_ids      = [aws_security_group.streamlit_sg.id]
  associate_public_ip_address = true

  user_data = file("${path.module}/user_data.sh")

  tags = {
    Name = "StreamlitApp"
  }
}
