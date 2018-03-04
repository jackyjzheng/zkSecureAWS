import OpenSSL
import boto3
import os
import json
import subprocess
import sys
from implementation.functions import *
from implementation.aws_setup import AWS_Setup

'''
Creating config file in .aws to connect boto3 to AWS. Working on encrypting and decrypting info.
'''
AWSConfigPath = os.path.expanduser("~") + '/.aws/credentials'
if not os.path.exists(AWSConfigPath):
	create_aws_config(AWSConfigPath)

'''
Grabbing CA Info. Working on better input validation.
'''
caCertPathInput = raw_input("Please enter the absolute file path for your CA cert. PEM file: ")
caKeyPathInput = raw_input("Please enter the absolute file path for your CA private key file: ")

'''
zkCertManager handles the local creation of certificates and signing operations
(1) Begin by creating CSR using Zymkey's private key.
(2) Next we sign the CSR with your CA to create a valid Zymkey Certificate.
'''
zkCertManager = zkCertManager(caCertPath=caCertPathInput, caKeyPath=caKeyPathInput)
zkCertManager.gen_zymkey_csr(csrFilename="zymkey.csr", destFilePath="./")
zkCertManager.sign_csr_with_ca(csrFilename="zymkey.csr", crtFilename="zymkey.crt", destFilePath="./")

'''
AWSCertManager handles the registration of certificates with AWS.
(1) Begin by generating an RSA certificate that will be signed by your CA.
(2) This certificate also encodes a registration code tied to your AWS account.
(3) The signed certificate is sent to Amazon to register your CA.
'''
AWSManager = AWSCertManager(caCertPath=caCertPathInput, caKeyPath=caKeyPathInput, deviceCertPath='zymkey.crt')
verificationPem = AWSManager.gen_verify_csr()
with open("verify.csr", 'w') as f:
  f.write(verificationPem)
zkCertManager.sign_csr_with_ca(csrFileName="verify.csr", crtFileName="verify.crt", destFilePath="./", )
if AWS_Manager.register_CA_AWS(verify_crt_path="verify.crt") == -1:
	sys.exit()
AWSsetup = AWS_Setup()
AWSsetup.sigSetup()
AWSsetup.dbSetup()

'''
We finish by registering Zymkey cert and getting it functional.
(1) Register Zymkey device certificate with AWS IoT simply by presenting it to AWS.
(2) Create and attach policy to this certificate allowing it to publish data
'''
zkRegisterReponse = AWSManager.register_device_cert_AWS()
AWSManager.publish_cert_id(zkRegisterReponse)
AWSManager.create_initial_policy(targetARN=zkRegisterResponse['certificateArn'])