module "dynamodb" {
  source = "./modules/dynamodb"
}

module "s3_bucket" {
  source = "./modules/s3"
}

module "api_crawler" {
  source = "./modules/api_crawler"

  collected_sites_table_arn  = module.dynamodb.collected_sites_table_arn
  collected_sites_table_name = module.dynamodb.collected_sites_table_name
}

module "url_crawler" {
  source = "./modules/url_crawler"

  ssh_key_name = module.ansible.ssh_key_name
  collected_sites_table_arn = module.dynamodb.collected_sites_table_arn
  collected_sites_table_name = module.dynamodb.collected_sites_table_name
}

module "ansible" {
  source = "./modules/ansible"

  url_crawler_public_ip = module.url_crawler.url_crawler_public_ip
}