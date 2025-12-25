resource "docker_image" "prometheus" {
  name = "prom/prometheus:latest"
}

resource "docker_container" "prometheus" {
  name  = "prometheus"
  image = docker_image.prometheus.latest
  ports {
    internal = 9090
    external = 9090
  }
  volumes {
    host_path      = "${path.module}/prometheus.yml"
    container_path = "/etc/prometheus/prometheus.yml"
  }
}

resource "local_file" "prometheus_config" {
  filename = "${path.module}/prometheus.yml"
  content  = <<EOF
# Prometheus config
global:
  scrape_interval: 15s
scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
EOF
}
