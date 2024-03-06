#!/bin/bash

# This script installs additional dependencies required for the test

sudo apt-get update
sudo apt-get install -y coinor-cbc coinor-libcbc-dev
sudo apt-get install -y glpk-utils
