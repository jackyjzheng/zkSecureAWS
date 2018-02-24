import boto3
import ecdsa
import hashlib
import os

def verify_ecdsa_signature(data, sig, pub_key):
	vk = ecdsa.VerifyingKey.from_pem(pub_key)
	return vk.verify(sig, data, hashfunc=hashlib.sha256)

def lambda_handler(event, context):
	pub_key_pem = '-----BEGIN PUBLIC KEY-----\n'
	pub_key_pem += (os.environ['new_pub_key'].decode("hex").encode("base64")) 
	pub_key_pem += '-----END PUBLIC KEY-----'
	print(pub_key_pem)
	signature = "99a25bf5f0ccf9abed74553ab38800bd043ed7a5ccfb6ceb28b53db1dead3b09755141c8c1478362796d28ee1e0e50b063f5db5a9976bc276c46c4a1f00b0472"

	if verify_ecdsa_signature(data=bytearray('hello'), sig=bytearray.fromhex(signature), pub_key=pub_key_pem):
		print('Signature matches data and public key pair.')
		dynamodb = boto3.resource('dynamodb') 
		table = dynamodb.Table('IoT')
		table.put_item(Item = event)
	else:
		print('Signature is invalid; it does not correspond to the public key.')