#!/bin/sh

sudo apt-get update
sudo apt-get install OpenSSL
sudo apt-get install libcurl4-openssl-dev libcurl4-openssl-dev
sudo apt-get install python-openssl

pip install boto3
pip install pycurl