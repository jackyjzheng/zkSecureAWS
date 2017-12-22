import json
import ecdsa
import hashlib
import pycurl
import sensor as sensor
	
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
	c.setopt(c.CAINFO, CA_Path
	
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
	)

	c.perform()

if name == '__main__':
	os.system('modprobe w1-gpio')
	os.system('modprobe w1-therm')
	base_dir = '/sys/bus/w1/devices/'
	device_folder = glob.glob(base_dir + '28*')[0]
	device_file = device_folder + '/w1_slave'	
		
	AWS_ENDPOINT = 'https://ar21wpwmha9rv.iot.us-west-2.amazonaws.com:8443/topics/pub_key_validate?qos=1'
	
	while True:
		post_field = sensor.collect_and_sign_data(device_file)
		ZK_AWS_Publish(url=AWS_ENDPOINT, post_field=json_data, CA_Path='/home/pi/Desktop/AWS_CA.pem', Cert_Path='/home/pi/Desktop/zymkey.crt')
