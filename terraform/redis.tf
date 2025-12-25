# Redis Terraform configuration

provider "docker" {
  host = "unix:///var/run/docker.sock"
}

resource "docker_network" "redis_network" {
  name = "redis_network"
}

resource "docker_container" "redis" {
  image = "redis:7"
  name  = "redis-server"
  restart = "unless-stopped"
  networks_advanced {
    name = docker_network.redis_network.name
  }
  ports {
    internal = 6379
    external = 6379
  }
}

output "redis_url" {
  value = "redis://localhost:6379"
}
