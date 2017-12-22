import OpenSSL
import boto3
import os
import subprocess
import aws_functions as aws_functions 

#Need better argument validation
ca_cert_path = Input("Please enter the absolute file path for your CA pem file.")
ca_key_path = Input("Please enter the absolute file path for you CA cert file.")

#Creating Zymkey device certificate csr
csr_filename = "zymkey.csr"
subprocess.check_call(['./bash_scripts/gen_csr.sh', csr_filename])

#Signing Zymkey csr to create device certificate
crt_filename = "zymkey.crt"
subprocess.check_call(['./bash_scripts/sign_csr.sh', ca_cert_path, ca_key_path, csr_filename, crt_filename])

#Registering CA on AWS IoT
aws_functions.register_CA_AWS(CA_cert_path, CA_key_path)	

#Registering Zymkey device certificate with AWS IoT
aws_functions.activate_cert_AWS(CA_path, Cert_path)

#Attach policy to this certificate allowing it to publish data


