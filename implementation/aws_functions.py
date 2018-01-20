import OpenSSL
import boto3
import os

def gen_AWS_verification_csr(registrationCode):
	key = OpenSSL.crypto.PKey()
	key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
	req = OpenSSL.crypto.X509Req()
	req.get_subject().CN = registrationCode
	req.set_pubkey(key)
	req.sign(key, "sha256")	
	return OpenSSL.crypto.dump_certificate_request(OpenSSL.crypto.FILETYPE_PEM, req)

def sign_CSR_with_CA(verification_csr, CA_cert_path, CA_key_path):
	ca_cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, open(CA_cert_path).read())
	ca_key = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, open(CA_key_path).read())
	req = OpenSSL.crypto.load_certificate_request(OpenSSL.crypto.FILETYPE_PEM, verification_csr)
	cert = OpenSSL.crypto.X509()
	cert.set_subject(req.get_subject())
	cert.set_serial_number(1)
	cert.gmtime_adj_notBefore(0)
	cert.gmtime_adj_notAfter(24 * 60 * 60)
	cert.set_issuer(ca_cert.get_subject())
	cert.set_pubkey(req.get_pubkey())
	cert.sign(ca_key, "sha256")
	return OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)

def register_CA_AWS(CA_cert_path, CA_key_path):
	client = boto3.client('iot')
	
	response = client.get_registration_code()
	registration_key = response['registrationCode']
	
	verification_pem = gen_AWS_verification_csr(registrationCode=registration_key)
	verification_cert = sign_CSR_with_CA(verification_csr=verification_pem, CA_cert_path=CA_cert_path, CA_key_path=CA_key_path)
	
	response = client.register_ca_certificate(
		caCertificate=open(CA_cert_path).read(),
		verificationCertificate=verification_cert,
		setAsActive=True,
		allowAutoRegistration=True
	)

	return response

def activate_cert_AWS(CA_path, Cert_path):
	boto3client = boto3.client('iot')
	with open(CA_path) as CA_file:
               CA_Pem = CA_file.read()
        with open(Cert_path) as Cert_file:
                Cert_Pem = Cert_file.read()
        return boto3client.register_certificate(
		certificatePem=Cert_Pem,
		caCertificatePem=CA_Pem,
		setAsActive=True,
	)

