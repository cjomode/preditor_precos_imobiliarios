output "instance_public_ip" {
  description = "IP público da EC2 para acessar o Streamlit"
  value       = aws_instance.streamlit_instance.public_ip
}
