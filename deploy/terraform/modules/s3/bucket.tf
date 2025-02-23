resource "aws_s3_bucket" "public_bucket" {
  bucket = "phishing-browser-screenshots" # Remplacez par un nom unique pour le bucket

  tags = {
    Name        = "Phishing browser screenshots"
    Environment = "Prod"
  }
}

resource "aws_s3_bucket_policy" "public_bucket_policy" {
  bucket = aws_s3_bucket.public_bucket.id

  policy = <<EOT
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::${aws_s3_bucket.public_bucket.id}/*"
    }
  ]
}
EOT
}

resource "aws_s3_bucket_public_access_block" "public_access_block" {
  bucket = aws_s3_bucket.public_bucket.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = true
  restrict_public_buckets = false
}