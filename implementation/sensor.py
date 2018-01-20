import zymkey
import binascii
import json
import time
import glob
import os


def read_temp_raw(device_file):
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines


def read_temp(device_file):
	lines = read_temp_raw(device_file)
	while lines[0].strip()[-3:] != 'YES':
		time.sleep(0.2)
		lines = read_temp_raw()
	equals_pos = lines[1].find('t=')
	if equals_pos != -1:
		temp_string = lines[1][equals_pos+2:]
		temp_c = float(temp_string) / 1000.0
		temp_f = temp_c * 9.0 / 5.0 + 32.0
		return temp_c, temp_f


'''
The following functions collects temperature data, signs and returns the following json:
	"{
		'data': 'hex_string of data',
		'signature': 'hex_string of signature;
	}"
'''

def collect_and_sign_data(device_file):
	temp = read_temp()
	temp_F = temp[1], temp_C = temp[0]
	deviceID = 1, myIP= '169.231.116.56'
	
	#Package the data in Python dictionary, then convert to JSON string.
	data = {'temp_F': temp_F, 'temp_C': temp_C, 'deviceIP': myIP, 'deviceID': deviceID}
	
	#Encrypt the underlying bytes for the string and then sign it.
	encrypted_data = zymkey.client.lock(bytearray(json.dumps(data)))
	signature = zymkey.client.sign(encrypted_data)

	#Make a new dictionary to hold the hex_strings of the encrypted data and signture, and then turn into JSON
	json_data = json.dumps({'data': binascii.hexlify(encrypted_data), 'signature': binascii.hexlify(signature)})
	return json_data	
