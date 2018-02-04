import zipfile
import boto3
import os

def createLambdaFunction(lambdaFileName):
	iam_client = boto3.client('iam');

	cur_dir = os.path.dirname(__file__)
	trustFilePath = cur_dir + '/policies/trust_document.txt'

	with open(trustFilePath) as trust_role:
		trust_document = trust_role.read()

	# Creating the IAM role with the specified Trust
	create_role_response = iam_client.create_role(
		RoleName = 'lambda_dynamo_role',
		AssumeRolePolicyDocument = trust_document,
		Description = 'AWS role given to lambda'
	)

	attach_response = iam_client.attach_role_policy(
		RoleName = 'lambda_dynamo_role',
		PolicyArn = 'arn:aws:iam::aws:policy/service-role/AWSLambdaDynamoDBExecutionRole'
	)

	# Download the zip file with the lambda code and save it in the same directory as this script.
	fileNoPy = lambdaFileName.replace(' ', '')[:-3] # Remove the .py extension from the file
	lambdaCodeDir = cur_dir + '/lambda_sourcecode/'
	filePath = lambdaCodeDir + lambdaFileName
	fileNoPyPath = lambdaCodeDir + fileNoPy
	zipfile.ZipFile(fileNoPyPath + '.zip', mode='w').write(filePath)

	with open(fileNoPyPath + '.zip', mode='rb') as file:   
		filecontent = file.read()

	print(attach_response)
	lambda_client = boto3.client('lambda')
	create_lambda_response = lambda_client.create_function(
		FunctionName=lambdaFileName,
		Runtime='nodejs4.3',
		#By appending this script unto create_jitr_lambda.py you do not need to find the role_ARN, as it will already be stored in this object.
		Role='lambda_dynamo_role',
		Handler='index.handler	',
		Code={
			'ZipFile': filecontent
		},
		Description='Lambda function for publishing data from IoT to DynamoDB',
	)