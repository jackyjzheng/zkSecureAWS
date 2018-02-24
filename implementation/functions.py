import OpenSSL
import boto3
import os
import subprocess

def read_from_file(file_path):
    '''
    Simple function to return contents in file as string.
    '''
    with open(file_path, 'r') as input_file:
        string_text = input_file.read()
    return string_text

class Zymkey_Cert_Manager(object):
    def __init__(self, ca_cert_path="", ca_key_path=""):
        self.ca_cert = (ca_cert_path)
        self.ca_key = (ca_key_path)

    """
    HELPER FUNCTIONS
    """
    def gen_zymkey_csr(self, fileName, filePath): #Add filepath to store csr later	
        subprocess.check_call(['./bash_scripts/gen_csr.sh', fileName, filePath])

    def sign_csr_with_ca(self, filePath, csr_name, crt_name):
        '''
        Invokes sign_csr bash script.
        '''
        subprocess.check_call(['./bash_scripts/sign_csr.sh', self.ca_cert, self.ca_key, filePath, csr_name, crt_name])

    def gen_zymkey_cert(self, filePath, crt_name):
        gen_zymkey_csr("zymkey.csr", "./")
        sign_csr_with_ca("./", "zymkey.csr", "zymkey.crt")
    
class AWS_Cert_Manager(object):
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
        self.device_path = device_cert_path
        self.ca_cert = read_from_file(ca_cert_path)
        self.ca_key = read_from_file(ca_key_path)
        self.device_cert = read_from_file(device_cert_path)
    
    def gen_verify_csr(self):
        '''
        Generate a CSR file using OpenSSL with CN=registration_code. This will be signed by CA and sent to Amazon to verify you can sign with CA.
        '''
        client = boto3.client('iot')
        response = client.get_registration_code()
        registration_key = response['registrationCode']
        
        key = OpenSSL.crypto.PKey()
        key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
        req = OpenSSL.crypto.X509Req()
        req.get_subject().CN = registration_key
        req.set_pubkey(key)
        req.sign(key, "sha256")	
        return OpenSSL.crypto.dump_certificate_request(OpenSSL.crypto.FILETYPE_PEM, req)

    """
    MAIN FUNCTIONS
    """
    def register_CA_AWS(self, verify_crt_path):
        '''
        Registers your CA with your AWS IoT accuont
        '''
        client = boto3.client('iot')
        with open(verify_crt_path, 'r') as f:
            verification_cert=f.read()
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
		with open(self.ca_path) as CA_file:
               		CA_Pem = CA_file.read()
        	with open(self.device_path) as Cert_file:
                	Cert_Pem = Cert_file.read()
        	return boto3client.register_certificate(
			certificatePem=self.device_cert,
			caCertificatePem=self.ca_cert,
			status="ACTIVE"
		)
    def create_initial_policy(self, targetARN):
		'''
		Creates a policy for your device to connect and publish data to AWS IoT
		'''
		client = boto3.client('iot')
                with open("implementation/policies/iot_policy.txt") as policy_json:
			policy = policy_json.read()
		response = client.create_policy(
			policyName='IoTPublishPolicy',
			policyDocument=policy
		
		)
                print(response)
		return client.attach_policy(
			policyName='IoTPublishPolicy',
			target=targetARN
		)            
