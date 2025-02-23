output "collected_sites_table_arn" {
  value = aws_dynamodb_table.collected_sites_table.arn
}

output "collected_sites_table_name" {
  value = aws_dynamodb_table.collected_sites_table.name
}