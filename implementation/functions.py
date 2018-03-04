import OpenSSL
import boto3
import os
import subprocess
from aws_config_manager import AWS_Config_Manager
from botocore.exceptions import ClientError

def read_from_file(filePath):
  '''
  Simple function to return contents in file as string.
  '''
  with open(filePath, 'r') as inputFile:
    stringText = inputFile.read()
  return stringText

def create_aws_config(AWSCredentialsPath):
  AWSKeyId = raw_input("Please enter your AWS Key id: ")
  AWSSecretKey = raw_input("Please enter your AWS secret key: ")
  AWSRegion = raw_input("Please enter your AWS Region: ")
  with open(AWSCredentialsPath, 'w') as f:
    f.write("[default]\n")
    f.write("aws_access_key_id = " + AWSKeyId + "\n")
    f.write("aws_secret_access_key = " + AWSSecretKey + "\n")
    f.write("region=" + AWSRegion)

class zkCertManager(object):
  def __init__(self, caCertPath="", caKeyPath=""):
    self.caCert = (caCertPath)
    self.caKey = (caKeyPath)

  """
  HELPER FUNCTIONS
  """
  def gen_zymkey_csr(self, csrFilename, destFilePath): #Add filepath to store csr later  
    print("---Generating Zymkey Certificate, Enter your Certificate Info---")
    subprocess.check_call(['./bash_scripts/gen_csr.sh', csrFilename, destFilePath])

  def sign_csr_with_ca(self, csrFilename, crtFilename, destFilePath):
    '''
    Invokes sign_csr bash script.
    '''
    subprocess.check_call(['./bash_scripts/sign_csr.sh', self.caCert, self.caKey, destFilePath, csrFilename, crtFilename])

  def gen_zymkey_cert(self, crtFilename, destFilePath):
    gen_zymkey_csr(csrFileName="zymkey.csr", destFilepath="./")
    sign_csr_with_ca(csrFilename="zymkey.csr", crtFilename="zymkey.crt", destFilePath="./")
    
class AWSCertManager(object):
  """
  CLASS ATTRIBUTES:
      ca_path=filepath of your CA pem file.
      ca_key_path=filepath of your CA private key file.
      ca_cert=PEM of your CA certificate in string format.
      ca_key=PEM of your CA private key in string format.
      device_cert=PEM of your Zymkey device certificate in string format.
  """
  def __init__(self, caCertPath="", caKeyPath="", deviceCertPath=""):
    self.caPath = caCertPath
    self.caKeyPath = caKeyPath
    self.zkCertPath = deviceCertPath
    self.caCert = read_from_file(caCertPath)
    self.caKey = read_from_file(caKeyPath)
    self.zkCert = read_from_file(deviceCertPath)
    self.AWSConfig = AWS_Config_Manager()
  
  def gen_verify_csr(self):
    '''
    Generate a CSR file using OpenSSL with CN=registration_code. This will be signed by CA and sent to Amazon to verify you can sign with CA.
    '''
    print("---Generating RSA Certificate for Amazon validation---")
    client = boto3.client('iot')
    response = client.get_registration_code()
    registrationKey = response['registrationCode']
    
    key = OpenSSL.crypto.PKey()
    key.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)
    req = OpenSSL.crypto.X509Req()
    req.get_subject().CN = registrationKey
    req.set_pubkey(key)
    req.sign(key, "sha256") 
    return OpenSSL.crypto.dump_certificate_request(OpenSSL.crypto.FILETYPE_PEM, req)

  """
  MAIN FUNCTIONS
  """
  def register_CA_AWS(self, verifyCertPath):
    '''
    Registers your CA with your AWS IoT accuont
    '''
    print("---Registering your CA with AWS IoT---")
    client = boto3.client('iot')
    with open(verifyCertPath, 'r') as f:
      verificationCert=f.read()
    try:
      response = client.register_ca_certificate(
        caCertificate=self.caCert,
        verificationCertificate=verificationCert,
        setAsActive=True,
        allowAutoRegistration=True
      )
      self.AWSConfig.setIotCA(response['certificateId'])
      return response
    except ClientError as e:
      errorCode = e.response['Error']['Code']
      if errorCode == 'ResourceAlreadyExistsException':
        print('CA already exists...skipping CA creation and updating CA arn in ~/.aws/zymkeyconfig...')
        if self.AWSConfig.iot_ca == '':
          print('Cannot get the existing CA from ~/.aws/zymkeyconfig... Manually update ~/.aws/zymkeyconfig yourself')
          print('FAILURE...exiting script...')
          return -1 # CA exists in AWS, but not specified in the zymkeyconfig
        else:
          return 0 # CA exists in AWS, and is correctly specified in zymkeyconfig so we continue
      else:
        print(e)
    except Exception as e:
      print(e)
  
  def register_device_cert_AWS(self):
    '''
    Register your certificate as a valid 'device' on AWS IoT
    '''
    boto3Client = boto3.client('iot')
    with open(self.caPath) as caFile:
      caPem = cafile.read()
    with open(self.zkCertPath) as certFile:
      certPem = certFile.read()
    response = boto3client.register_certificate(
      certificatePem=self.zkCert,
      caCertificatePem=self.caCert,
      status="ACTIVE"
    )
    self.AWSConfig.setIotCert(response['certificateArn'])
    return response

  def publish_cert_id(certCreateResponse):
    '''
    Publish certificate ID to certID topic to trigger lambda.
    '''
    publishCertClient = boto3.client('iot-data')
    publishCertClient.publish(
      topic='certID',
      qos=1,
      payload=json.dumps(certCreateReponse)
    ) 
  
  def create_initial_policy(self, targetARN):
    '''
    Creates a policy for your device to connect and publish data to AWS IoT
    '''
    policyName = 'IoTPublishPolicy'
    client = boto3.client('iot')
    with open("implementation/policies/iot_policy.txt") as policyJson:
      policy = policyJson.read()
    try:
      response = client.create_policy(
        policyName=policyName,
        policyDocument=policy
      )
      attachResponse = client.attach_policy(
        policyName=policyName,
        target=targetARN
      )
      self.AWSConfig.setIotPolicy(response['policyArn'])
      return attachResponse
    except ClientError as e:
      errorCode = e.response['Error']['Code']
      if errorCode == 'ResourceAlreadyExistsException':
        print('IoT policy already exists...skipping IoT policy creation and updating policy name in ~/.aws/zymkeyconfig...')
        getResponse = client.get_policy(policyName = policyName)
        self.AWConfig.setIotPolicy(getResponse['policyArn'])
        return client.attach_policy(
          policyName = policyName,
          target = targetARN
        )
      else:
        print(e)
    except Exception as e:
      print(e)

