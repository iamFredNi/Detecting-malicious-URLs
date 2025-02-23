resource "tls_private_key" "ssh_keys" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "local_sensitive_file" "ssh_private_key_file" {
  filename = "${path.module}/../../../ansible/ssh_private_key"
  content  = tls_private_key.ssh_keys.private_key_pem
}

resource "aws_key_pair" "ssh_key_pair" {
  key_name   = "honeypot_ssh_keys"
  public_key = tls_private_key.ssh_keys.public_key_openssh
}