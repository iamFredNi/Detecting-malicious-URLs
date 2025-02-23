resource "local_file" "hosts_file" {
  filename = "${path.module}/../../../ansible/hosts.ini"
  content = templatefile("${path.module}/hosts.ini.tftpl", {
    honeypot_ip_addr    = var.honeypot_public_ip,
    url_crawler_ip_addr = var.url_crawler_public_ip,
  })
}
