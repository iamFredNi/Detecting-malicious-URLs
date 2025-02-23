resource "aws_iam_role" "scheduler_role" {
  name = "phishing-browser-prod-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "allow"
        Principal = {
          Service = "scheduler.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "scheduler_invoke_policy" {
  name = "phishing-browser-prod-scheduler-policy"
  role = aws_iam_role.scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["lambda:InvokeFunction"]
        Effect   = "Allow"
        Resource = aws_lambda_function.lambda_api_crawler.arn
      }
    ]
  })
}

resource "aws_scheduler_schedule" "lambda_cron_event" {
  name = "phishing-browser-prod-lambda-scheduler"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = "rate(1 hours)"

  target {
    arn      = aws_lambda_function.lambda_api_crawler.arn
    role_arn = aws_iam_role.scheduler_role.arn
  }
}