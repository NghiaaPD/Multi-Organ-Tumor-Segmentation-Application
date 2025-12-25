# PostgreSQL Terraform configuration

provider "docker" {
  host = "unix:///var/run/docker.sock"
}

resource "docker_network" "postgres_network" {
  name = "postgres_network"
}

resource "docker_volume" "postgres_data" {
  name = "postgres_data"
}

resource "docker_container" "postgres" {
  image = "postgres:15"
  name  = "postgres-server"
  restart = "unless-stopped"
  networks_advanced {
    name = docker_network.postgres_network.name
  }
  volumes {
    volume_name    = docker_volume.postgres_data.name
    container_path = "/var/lib/postgresql/data"
  }
  env = [
    "POSTGRES_USER=admin",
    "POSTGRES_PASSWORD=admin123",
    "POSTGRES_DB=appdb"
  ]
  ports {
    internal = 5432
    external = 5432
  }
}

output "postgres_url" {
  value = "postgresql://admin:admin123@localhost:5432/appdb"
}
output "postgres_user" {
  value = "admin"
}
output "postgres_password" {
  value = "admin123"
}
output "postgres_db" {
  value = "appdb"
}
