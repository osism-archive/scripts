variable "name" {}
variable "pubkey" {}
variable "image" {}
variable "flavor" {}
variable "network" {}

resource "openstack_compute_instance_v2" "instance" {
  name            = var.name 
  image_name      = var.image
  flavor_name     = var.flavor
  key_pair        = var.pubkey
  
  network {
    name = var.network
  }

  provisioner "remote-exec" {
    connection {
      type        = "ssh"
      host        = self.access_ip_v4
      user        = "install"
      private_key = file(pathexpand("~/.ssh/id_rsa"))
    }

    inline = ["cat /etc/machine-id"]
  }
}
