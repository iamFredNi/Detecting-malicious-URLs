resource "aws_iam_role" "url_crawler_instance_role" {
  name = "phishing-browser-url-crawler-instance-role"

  assume_role_policy = jsonencode({
    "Version" : "2012-10-17"
    "Statement" = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = {
    Environment = "Prod"
    App         = "Phishing-Browser"
  }
}

resource "aws_iam_policy" "url_crawler_dynamodb_policy" {
  name        = "phishing-browser-url-crawler-dynamodb-policy"
  description = "Policy to allow url crawler instance to access DynamoDB"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = [
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:GetItem",
        "dynamodb:DescribeTable",
        "dynamodb:Scan"
      ]
      Effect   = "Allow"
      Resource = var.collected_sites_table_arn
      }, {
      Action = [
        "secretsmanager:ListSecrets",
        "secretsmanager:DescribeSecret",
        "secretsmanager:GetSecretValue",
      ]
      Effect   = "Allow"
      Resource = [
        "arn:aws:secretsmanager:eu-west-3:209208331320:secret:phishing-brower/prod/reddit-api-z1zEXU",
        "arn:aws:secretsmanager:eu-west-3:209208331320:secret:phishing-browser/prod/checker_api_keys-zzAkEB"
      ]
      }, {
        Action = [
          "s3:ListBucket",
          "s3:GetObject",
          "s3:DeleteObject",
          "s3:PutObject",
        ]
        Effect = "Allow"
        Resource = [
          "arn:aws:s3:::phishing-browser-screenshots",
          "arn:aws:s3:::phishing-browser-screenshots/*"
        ]
      }
    ]
  })

  tags = {
    Environment = "Prod"
    App         = "Phishing-Browser"
  }
}

resource "aws_iam_role_policy_attachment" "url_crawler_role_dynamodb_attach" {
  role       = aws_iam_role.url_crawler_instance_role.name
  policy_arn = aws_iam_policy.url_crawler_dynamodb_policy.arn
}

resource "aws_iam_instance_profile" "url_crawler_instance_profile" {
  name = "phishing-brower-url-crawler-instance-profile"
  role = aws_iam_role.url_crawler_instance_role.name
}