resource "aws_iam_role" "lambda_exec_role" {
  name = "phishing-browser-lambda-exec-role"

  assume_role_policy = jsonencode({
    "Version" : "2012-10-17"
    "Statement" = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = {
    Environment = "Prod"
    App         = "Phishing-Browser"
  }
}

resource "aws_iam_policy" "lambda_dynamodb_policy" {
  name        = "phishing-browser-lambda-dynamodb-policy"
  description = "Policy to allow Lambda to access DynamoDB"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = [
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:GetItem"
      ]
      Effect   = "Allow"
      Resource = var.collected_sites_table_arn
      }, {
      Action = [
        "secretsmanager:GetSecretValue",
      ]
      Effect   = "Allow"
      Resource = "arn:aws:secretsmanager:eu-west-3:209208331320:secret:phishing-brower/prod/reddit-api-z1zEXU"
    }]
  })

  tags = {
    Environment = "Prod"
    App         = "Phishing-Browser"
  }
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb_attach" {
  role       = aws_iam_role.lambda_exec_role.name
  policy_arn = aws_iam_policy.lambda_dynamodb_policy.arn
}