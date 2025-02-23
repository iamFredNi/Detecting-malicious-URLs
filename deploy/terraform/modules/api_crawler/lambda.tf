resource "aws_lambda_layer_version" "dependency_layer" {
  layer_name = "phishing-browser-prod-dep-layer"

  filename = "../layer.zip"

  compatible_runtimes = ["python3.9"]
}

resource "aws_lambda_function" "lambda_api_crawler" {
  function_name = "Phishing-Browser-API-Crawler"
  role          = aws_iam_role.lambda_exec_role.arn
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"

  filename = "../lambda_function.zip"

  layers = [aws_lambda_layer_version.dependency_layer.arn]

  timeout = 300

  environment {
    variables = {
      TABLE_NAME = var.collected_sites_table_name
    }
  }

  tags = {
    Environment = "Prod"
    App         = "Phishing-Browser"
  }
}