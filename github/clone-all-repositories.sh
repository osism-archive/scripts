#!/bin/sh
#
# Script to clone all repositories from one organization into the current directory
#
####################################################################################################
token=<put_your_github_access_token_here>
orga=osism

for i in $(curl -s -u tibeer:${token} -H "Accept: application:vnd.github.v3+json" 'https://api.github.com/orgs/'${orga}'/repos?per_page=100' | jq '.[].name' | sed 's/"//g'); do
  git clone git@github.com:${orga}/${i}.git
done
