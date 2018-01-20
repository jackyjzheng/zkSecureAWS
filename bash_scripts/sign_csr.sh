#!/bin/bash
set -e

SCRIPT_NAME=$(basename $0)

[ -z $2 ] && echo "${SCRIPT_NAME} <csr filename> <crt filename>" 1>&2 && exit 1

ca_pem=$1
ca_key=$2
csr=$3
crt=$4

cd certificates
openssl x509 -req -SHA256 -days 3650 \
  -CA ${ca_pem} -CAkey ${ca_key} -CAcreateserial \
  -in ${csr} -out ${crt}
