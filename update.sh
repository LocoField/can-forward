#!/bin/sh

sudo systemctl stop can-forward

git pull origin main
git rev-parse --short HEAD

sudo systemctl start can-forward
