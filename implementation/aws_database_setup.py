import boto3
import datetime

class AWS_DB_Setup:

  def __init__(self):
    self.dynamodb = boto3.resource('dynamodb')

  # Config (access_key, secret_key, region specified in the ~/.aws/ directory)
  def createTable(self, tableName):
    table = self.dynamodb.create_table(
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
    table.meta.client.get_waiter('table_exists').wait(TableName=tableName)

  def loadSampleData(self, tableName):
    table = self.dynamodb.Table(tableName)
    timestamp = datetime.datetime.now()
    table.put_item(
      Item = {
        'deviceId' : '1234',
        'timestamp' : str(timestamp),
        'data' : {
          'ip' : '192.168.12.28',
          'signature' : 'TESTSIGNATURE',
          'encryptedData' : 'ENCRYPTEDTEST',
          'tempData' : {
            'tempC' : 0,
            'tempF' : 32
          }
        }
      }
    )

  def loadCustomData(self, tableName, deviceId, ip, signature, encryptedData, tempC, tempF):
    table = self.dynamodb.Table(tableName)
    timestamp = datetime.datetime.now()
    table.put_item(
      Item = {
        'deviceId' : deviceId,
        'timestamp' : str(timestamp),
        'data' : {
          'ip' : ip,
          'signature' : signature,
          'encryptedData' : encryptedData,
          'tempData' : {
            'tempC' : tempC,
            'tempF' : tempF
          }
        }
      }
    )