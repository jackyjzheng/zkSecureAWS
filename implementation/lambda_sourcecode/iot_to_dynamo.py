def lambda_handler(event, ccontext):
	dynamodb = boto3.resource('dynamodb') 
	table = dynamodb.Table(tableName)
	table.put_item(
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
	)