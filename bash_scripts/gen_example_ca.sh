#!/bin/bash
set -e
mkdir CA_files
cd CA_files

openssl ecparam -genkey -name prime256v1 -out zk_ca.key
OPENSSL_CONF=/etc/ssl/openssl.cnf openssl req \
  -x509 -new -SHA256 -nodes -key zk_ca.key \
  -days 3650 -out zk_ca.crt \
  -subj "/C=US/ST=California/L=Santa Barbara/O=Zymkey/CN=zymkey-verify.zymbit.com.dev"

cp zk_ca.crt zk_ca.pem
