variable "counter" {}
variable "image" {}
variable "flavor" {}
variable "network" {}

locals {
  timestamp = formatdate("YYYY-MM-DD", timestamp())
}

data "local_file" "pubkey" {
  filename = pathexpand("~/.ssh/id_rsa.pub")
}

resource "openstack_compute_keypair_v2" "keypair" {
  name       = local.timestamp
  public_key = data.local_file.pubkey.content
}

module "instance" {
  source = "./instance"
  count  = var.counter
  
  name    = "instance_${count.index}__${local.timestamp}"
  pubkey  = openstack_compute_keypair_v2.keypair.name
  image   = var.image
  flavor  = var.flavor
  network = var.network
}

