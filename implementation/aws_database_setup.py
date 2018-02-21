import boto3
import datetime
from aws_config_manager import AWS_Config_Manager
from botocore.exceptions import ClientError

class AWS_DB_Setup:

  def __init__(self):
    self.dynamodb = boto3.resource('dynamodb')
    self.aws_config = AWS_Config_Manager()

  # Config (access_key, secret_key, region specified in the ~/.aws/ directory)
  def createTable(self, tableName):
    print('---Creating DynamoDB table...this may take up to 20 seconds---')
    try:
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
    except ClientError as e:
      error_code = e.response["Error"]["Code"]
      if error_code == "ResourceInUseException":
        print('Table already exists...skipping table creation and updating table name in /.aws/zymkeyconfig...')
    finally:
      self.aws_config.setTable(tableName)

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