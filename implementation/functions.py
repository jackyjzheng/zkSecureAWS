import openssl
import boto3
import os

class AWS_Cert_Activator:
	'''
	Attributes:
		ca_cert:
		ca_key:
		verification_csr:
	'''

	def __init__(self, name, ca_cert_path, ca_key_path, device_cert_path):
        	"""Return a Customer object whose name is *name* and starting
        	balance is *balance*."""
        	self.ca_cert = read_pem_from_file(ca_cert_path)
        	self.ca_key = read_pem_from_file(ca_key_path)
		self.device_cert = read_pem_from_file(device_cert_path)

	def read_pem_from_file(file_path)
		with open(file_path) as pem_file:
               		pem_string = pem_file.read()
		return pem_string
		
	def gen_verify_csr(registration_code)
		key = OpenSSL.crypto.PKey()
		key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
		req = OpenSSL.crypto.X509Req()
		req.get_subject().CN = registrationCode
		req.set_pubkey(key)
		req.sign(key, "sha256")	
		return OpenSSL.crypto.dump_certificate_request(OpenSSL.crypto.FILETYPE_PEM, req)

	def sign_csr_with_ca():
		subprocess.check_call(['./bash_scripts/sign_csr.sh', ca_cert_path, ca_key_path, csr_filename, crt_filename])

	def register_CA_AWS(CA_cert_path, CA_key_path):
		client = boto3.client('iot')
		response = client.get_registration_code()
		registration_key = response['registrationCode']
	
		verification_pem = gen_AWS_verification_csr(registrationCode=registration_key)
		'fix'
		verification_pem = sign_csr_with_ca()
	
		response = client.register_ca_certificate(
			caCertificate=open(CA_cert_path).read(),
			verificationCertificate=verification_cert,
			setAsActive=True,
			allowAutoRegistration=True
		)
		return response

	def register_device_cert_AWS(Ca_path,Cert_path):
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

