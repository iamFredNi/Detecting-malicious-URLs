resource "aws_vpc" "main_vpc" {
  cidr_block = "20.0.0.0/24"

  tags = {
    Name        = "honeypot-vpc"
    App         = "Phishing-Browser"
    Environment = "Prod"
  }
}

resource "aws_subnet" "honeypot_subnet" {
  vpc_id = aws_vpc.main_vpc.id

  cidr_block = "20.0.0.128/25"

  tags = {
    Name        = "honeypot-subnet"
    App         = "Phishing-Browser"
    Environment = "Prod"
  }
}

resource "aws_instance" "honeypot_instance" {

  subnet_id                   = aws_subnet.honeypot_subnet.id
  associate_public_ip_address = true

  ami = "lol"

  key_name = var.ssh_key_name

  tags = {
    Name        = "honeypot-instance"
    App         = "Phishing-Browser"
    Environment = "Prod"
  }
}

resource "local_file" "ansible_hosts_ini_file" {
  filename = "${dirname}/hosts.ini"
  content  = templatefile("./hosts.ini.tftpl", { honeypot_public_ip = aws_instance.honeypot_instance.public_ip })
}