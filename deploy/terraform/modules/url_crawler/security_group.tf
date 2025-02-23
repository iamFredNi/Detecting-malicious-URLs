resource "aws_security_group" "url_crawler_allow_sg" {
  name        = "phishing-browser-url-crawler-sg"
  description = "Allow SSH traffic to the url crawler instance"

  vpc_id = aws_vpc.url_crawler_vpc.id
}

resource "aws_vpc_security_group_egress_rule" "allow_all_out" {
    security_group_id = aws_security_group.url_crawler_allow_sg.id

    cidr_ipv4 = "0.0.0.0/0"
    ip_protocol = "-1"
}

resource "aws_vpc_security_group_ingress_rule" "allow_ssh_in" {
  security_group_id = aws_security_group.url_crawler_allow_sg.id

  cidr_ipv4   = "0.0.0.0/0"
  from_port   = 22
  to_port     = 22
  ip_protocol = "tcp"
}