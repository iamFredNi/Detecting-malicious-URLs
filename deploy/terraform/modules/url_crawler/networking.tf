resource "aws_vpc" "url_crawler_vpc" {
  cidr_block = "100.0.0.0/24"

  tags = {
    Name        = "phishing-browser-url-crawler-vpc"
    environment = "Prod"
  }
}

resource "aws_subnet" "url_crawler_subnet" {
  vpc_id = aws_vpc.url_crawler_vpc.id

  cidr_block = "100.0.0.128/25"

  tags = {
    Name        = "phishing-browser-url_crawler-subnet"
    Environment = "Prod"
  }
}

resource "aws_internet_gateway" "url_crawler_igw" {
  vpc_id = aws_vpc.url_crawler_vpc.id
}

resource "aws_route_table" "url_crawler_subnet_rt" {
  vpc_id = aws_vpc.url_crawler_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.url_crawler_igw.id
  }
}

resource "aws_route_table_association" "url_crawler_rt_assoc" {
  subnet_id      = aws_subnet.url_crawler_subnet.id
  route_table_id = aws_route_table.url_crawler_subnet_rt.id
}