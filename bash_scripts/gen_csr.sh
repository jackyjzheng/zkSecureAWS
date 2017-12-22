#!/bin/bash
set -e 

csr_filename=$1
openssl req -key nonzymkey.key -new -out ${csr_filename} -engine zymkey_ssl -keyform e 
