variable "region" {
  description = "Região da AWS"
  default     = "us-east-1"
}

variable "instance_type" {
  description = "Tipo da instância EC2"
  default     = "t2.micro"
}

variable "key_name" {
  description = "Nome da chave SSH cadastrada na AWS"
  default     = "minha-chave"
}

variable "public_key_path" {
  description = "Caminho local da chave pública"
  default     = "~/.ssh/minha-chave.pub"
}

variable "repo_url" {
  description = "URL do repositório Git onde está o app.py"
  default     = "https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git"
}
