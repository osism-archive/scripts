#!/bin/sh
#
# Script to clone all repositories from one organization into the current directory
#
####################################################################################################
org=osism

gh repo list $org --limit 100 --json isArchived,sshUrl | jq '.[] | select( .isArchived == false)' | jq -r '.["sshUrl"]' | xargs -L1 git clone

