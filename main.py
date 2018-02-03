import OpenSSL
import boto3
import os
import subprocess
from implementation.functions import *

'''pip install boto3'''

aws_key_id = Input("Please enter your AWS Key id.")
aws_secret_key = Input("Please enter your AWS secret key.")
aws_region = Input("Please enter your AWS Region.")

aws_credentials_path = os.path.expanduser("~") + '/.aws/credentials'
with open(aws_credentials_path, 'w') as f:
  f.write("[default]")
  f.write("aws_access_key_id = " + aws_key_id)
  f.write("aws_secret_access_key = " + aws_secret_key)
  f.write("region=" + aws_region)

#Need better argument validation
ca_cert_path = Input("Please enter the absolute file path for your CA cert. PEM file.")
ca_key_path = Input("Please enter the absolute file path for your CA private key file.")

Zymkey_Manager = Zymkey_Cert_Manager(ca_cert_path, ca_key_path)
#Creating csr. with Zymkey private key
Zymkey.gen_zymkey_csr("./", "zymkey.csr")
#Signing Zymkey csr. to create device certificate
Zymkey.sign_csr_with_ca("./", "zymkey.crt")

AWS_Manager = AWS_Cert_Manager(ca_cert=ca_cert_path, ca_key=ca_key_path, device_cert='./bash_scripts/certificates/zymkey.crt')
#Registering CA on AWS IoT
AWS_Manager.register_CA_AWS()
#Registering Zymkey device certificate with AWS IoT
AWS_Manager.register_device_cert()
#Attach policy to this certificate allowing it to publish data


