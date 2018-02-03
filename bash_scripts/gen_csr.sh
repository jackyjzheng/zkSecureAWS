#!/bin/bash
set -e 
csr_filename=$1
file_path=$2
cd ${file_path}
openssl req -key nonzymkey.key -new -out ${csr_filename} -engine zymkey_ssl -keyform e
