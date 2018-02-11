import boto3

def lambda_handler(event, context):
	dynamodb = boto3.resource('dynamodb') 
	table = dynamodb.Table('IoT')

	table.put_item(Item = event)