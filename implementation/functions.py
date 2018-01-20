import openssl
import boto3
import os

class AWS_Cert_Activator(object):
	"""
	CLASS ATTRIBUTES:
		ca_path=filepath of your CA pem file.
		ca_key_path=filepath of your CA private key file.
		ca_cert=PEM of your CA certificate in string format.
		ca_key=PEM of your CA private key in string format.
		device_cert=PEM of your Zymkey device certificate in string format.
	"""

	def __init__(self, ca_cert_path="", ca_key_path="", device_cert_path=""):
        	self.ca_path = ca_cert_path
		self.ca_key_path = ca_key_path

		self.ca_cert = read_pem_from_file(ca_cert_path)
        	self.ca_key = read_pem_from_file(ca_key_path)
		self.device_cert = read_pem_from_file(device_cert_path)
	"""
	HELPER FUNCTIONS
	"""
	def read_from_file(file_path)
		'''
		Simple read text from file and outupt as string. 
		'''
		with open(file_path) as input_file:
               		string_text = input_file.read()
		return string_text
		
	def gen_verify_csr(registration_code)
		'''
		Generate a CSR file using OpenSSL with CN=registration_code. This will be signed by CA and sent to Amazon to verify you can sign with CA.
		'''
		key = OpenSSL.crypto.PKey()
		key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
		req = OpenSSL.crypto.X509Req()
		req.get_subject().CN = registrationCode
		req.set_pubkey(key)
		req.sign(key, "sha256")	
		return OpenSSL.crypto.dump_certificate_request(OpenSSL.crypto.FILETYPE_PEM, req)

	def sign_csr_with_ca(ca_cert_path, ca_key_path):
		'''
		Invokes sign_csr bash script.
		'''
		subprocess.check_call(['./bash_scripts/sign_csr.sh', ca_cert_path, ca_key_path, csr_filename, crt_filename])

	"""
	MAIN FUNCTIONS
	"""
	def register_CA_AWS(self):
		'''
		Registers your CA with your AWS IoT accuont
		'''
		client = boto3.client('iot')
		response = client.get_registration_code()
		registration_key = response['registrationCode']
	
		verification_pem = gen_AWS_verification_csr(registrationCode=registration_key)
		'fix'
		verification_cert = sign_csr_with_ca()
	
		response = client.register_ca_certificate(
			caCertificate=self.ca_cert,
			verificationCertificate=verification_cert,
			setAsActive=True,
			allowAutoRegistration=True
		)
		return response

	def register_device_cert_AWS(self):
		'''
		Register your certificate as a valid 'device' on AWS IoT
		'''
		boto3client = boto3.client('iot')
		with open(CA_path) as CA_file:
               		CA_Pem = CA_file.read()
        	with open(Cert_path) as Cert_file:
                	Cert_Pem = Cert_file.read()
        	return boto3client.register_certificate(
			certificatePem=self.device_cert,
			caCertificatePem=self.ca_cert,
			setAsActive=True,
		)

	def create_initial_policy():
		'''
		Creates a policy for your device to connect and publish data to AWS IoT
		'''
		client = boto3.client('iot')
		with open() as policy_json
			policy = policy_json.read()
		response = client.create_policy(
			policyName='IoTPublishPolicy',
			policyDocument=policy
		
		)
		response = client.attach_policy(
			policyName='IoTPublishPolicy',
			target=''
		)
