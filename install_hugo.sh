#!/usr/bin/env bash

# -e exit on non 0 return
set -e
# -u exit on undefined variables
set -u
# -x print command before running
set -x
# bubble up the non 0 on pipes
set -o pipefail

REPO="gohugoio/hugo"
FLAVOR="hugo"

LAST_GITHUB_V=$(curl -s https://api.github.com/repos/${REPO}/releases/latest | grep -oP '"tag_name": "\K(.*)(?=")')
DOWNLOAD_LINK="https://github.com/${REPO}/releases/download/${LAST_GITHUB_V}/${FLAVOR}_${LAST_GITHUB_V:1}_Linux-64bit.deb"
curl -L -o /tmp/hugo_install.deb $DOWNLOAD_LINK
sudo dpkg -i /tmp/hugo_install.deb
rm -rf /tmp/hugo_install.deb
hugo version
