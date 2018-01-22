import boto3

class AWS_DB_Setup:

	def __init__(self):
		pass

  # Config (access_key, secret_key, region specified in the ~/.aws/ directory)
	def createTable(self, tableName):
		dynamodb = boto3.resource('dynamodb')
		table = dynamodb.create_table(
    TableName = tableName,
    KeySchema = [
        {
            'AttributeName': 'deviceId',
            'KeyType': 'HASH'  #Partition key
        },
        {
            'AttributeName': 'timestamp',
            'KeyType': 'RANGE'  #Sort key
        }
    ],
    AttributeDefinitions = [
        {
            'AttributeName': 'deviceId',
            'AttributeType': 'S'
        },
        {
            'AttributeName': 'timestamp',
            'AttributeType': 'S'
        }
    ],
    ProvisionedThroughput = {
        'ReadCapacityUnits': 10,
        'WriteCapacityUnits': 10
    }
	)