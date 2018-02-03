import boto3

def lambda_handler(event, context):
  dynamodb = boto3.resource('dynamodb')
  tableName = 'IoT'
  Item = {
    'deviceId' : event.deviceId,
    'timestamp' : event.timestamp,
    'data' : {
      'ip' : event.data.ip,
      'signature' : event.data.signature,
      'encryptedData' : event.data.encryptedData,
      'tempData' : {
        'tempC' : event.data.tempData.tempC,
        'tempF' : event.data.tempData.tempF
      }
    }
  }
  table = dynamodb.Table(tableName)
  table.put_item(item)