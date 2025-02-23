resource "aws_dynamodb_table" "collected_sites_table" {
  name         = "CollectedSites"
  billing_mode = "PAY_PER_REQUEST"

  hash_key  = "id"
  range_key = "date"

  attribute {
    name = "id"
    type = "S"
  }

  attribute {
    name = "date"
    type = "S"
  }

  tags = {
    Environment = "Prod"
    App         = "Phishing-Browser"
  }
}