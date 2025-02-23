resource "aws_instance" "url_crawler_instance" {
  subnet_id                   = aws_subnet.url_crawler_subnet.id
  associate_public_ip_address = true

  instance_type = "t2.micro"
  ami           = "ami-0db5e28c1b3823bb7"
  iam_instance_profile = aws_iam_instance_profile.url_crawler_instance_profile.name

  key_name = var.ssh_key_name
  security_groups = [
    aws_security_group.url_crawler_allow_sg.id
  ]

  depends_on = [ aws_security_group.url_crawler_allow_sg ]
}