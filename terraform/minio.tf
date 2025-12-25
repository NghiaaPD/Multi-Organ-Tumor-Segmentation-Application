# MinIO Terraform configuration

provider "docker" {
  host = "unix:///var/run/docker.sock"
}

resource "docker_network" "minio_network" {
  name = "minio_network"
}

resource "docker_volume" "minio_data" {
  name = "minio_data"
}

resource "docker_container" "minio" {
  image = "minio/minio:latest"
  name  = "minio-server"
  restart = "unless-stopped"
  networks_advanced {
    name = docker_network.minio_network.name
  }
  volumes {
    volume_name    = docker_volume.minio_data.name
    container_path = "/data"
  }
  env = [
    "MINIO_ROOT_USER=minioadmin",
    "MINIO_ROOT_PASSWORD=minioadmin123"
  ]
  command = ["server", "/data", "--console-address", ":9001"]
  ports {
    internal = 9000
    external = 9000
  }
  ports {
    internal = 9001
    external = 9001
  }
}

output "minio_url" {
  value = "http://localhost:9000"
}
output "minio_console_url" {
  value = "http://localhost:9001"
}
output "minio_access_key" {
  value = "minioadmin"
}
output "minio_secret_key" {
  value = "minioadmin123"
}
