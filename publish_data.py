import json
import boto3
import hashlib
import binascii
import pycurl
from OpenSSL import SSL
import random
import zymkey

def ZK_AWS_Publish(url, post_field, CA_Path, Cert_Path,):
	#Setting Curl to use zymkey_ssl engine
	c = pycurl.Curl()
	c.setopt(c.SSLENGINE, "zymkey_ssl")
	c.setopt(c.SSLENGINE_DEFAULT, 1L)
	c.setopt(c.SSLVERSION, c.SSLVERSION_TLSv1_2)
	
	#Settings certificates for HTTPS connection
	c.setopt(c.SSLENGINE, "zymkey_ssl")
	c.setopt(c.SSLCERTTYPE, "PEM")
	c.setopt(c.SSLCERT, Cert_Path)
	c.setopt(c.CAINFO, CA_Path)
	
	#setting endpoint and HTTPS type, here it is a POST
	c.setopt(c.URL, url)
	c.setopt(c.POSTFIELDS, post_field)
	
	#Telling Curl to do client and host authentication
	c.setopt(c.SSL_VERIFYPEER, 1)
	c.setopt(c.SSL_VERIFYHOST, 2)
	
	#Turn on Verbose output and set key as placeholder, not actually a real file.
	c.setopt(c.VERBOSE, 1)
	c.setopt(c.SSLKEYTYPE, "ENG")	
	c.setopt(c.SSLKEY, "nonzymkey.key")
	c.perform()

if __name__ == "__main__":
    #os.system('modprobe w1-gpio')
    #os.system('modprobe w1-therm')
    #base_dir = '/sys/bus/w1/devices/'
    #device_folder = glob.glob(base_dir + '28*')[0]
    #device_file = device_folder + '/w1_slave'	
    boto3client = boto3.client('iot')
    topic = "demo"
    AWS_ENDPOINT = "https://" + str(boto3client.describe_endpoint()['endpointAddress']) + ":8443/topics/" + topic + "?qos=1"    
    device_id = 1
    ip = "192.168.12.28"
    while True:
        temp_data = {"tempF": random.randint(70,100), "tempC" : random.randint(35, 50)}
        encrypted_data = zymkey.client.lock(bytearray(json.dumps(temp_data)))
        signature = zymkey.client.sign(encrypted_data)
        data = {"ip": ip, "signature": binascii.hexlify(signature), "encryptedData": binascii.hexlify(encrypted_data), "tempData": temp_data}
        post_field = {"deviceId": device_id, "data": data}
        json_data = json.dumps(post_field)
        ZK_AWS_Publish(url=AWS_ENDPOINT, post_field=json_data, CA_Path='/home/pi/Zymkey-AWS-Kit/bash_scripts/CA_files/zk_ca.pem', Cert_Path='/home/pi/Zymkey-AWS-Kit/zymkey.crt')

