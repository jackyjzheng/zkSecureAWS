import boto3

def lambda_handler(event, context):
	dynamodb = boto3.resource('dynamodb') 
	table = dynamodb.Table('IoT')
	table.put_item(
	  Item = {
	    'deviceId' : event['deviceId'],
	    'timestamp' : event['timestamp'],
	    'data' : {
	      'ip' : event['data']['ip'],
	      'signature' : event['data']['signature'],
	      'encryptedData' : event['data']['encryptedData'],
	      'tempData' : {
	        'tempC' : event['data']['tempData']['tempC'],
	        'tempF' : event['data']['tempData']['tempF']
	      }
	    }
	  }
	)