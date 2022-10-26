#!/bin/bash
#
# Script to test ironic deployments with terraform
#
##########################################
cd /opt/terraform || exit 1
while true; do
  timestamp=$(date +"%Y-%m-%d-%H-%M")
  OS_CLOUD=testbed /opt/terraform/terraform apply -auto-approve > "logs/${timestamp}_apply.log"
  echo "sleep 5 seconds after apply"
  sleep 5
  OS_CLOUD=testbed /opt/terraform/terraform destroy -auto-approve > "logs/${timestamp}_destroy.log"
  echo "sleep 5 seconds after destroy"
  sleep 5
done

