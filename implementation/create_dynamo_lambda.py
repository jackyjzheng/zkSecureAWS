import zipfile
import boto3
import os
from os.path import basename
import time

def createLambdaFunction(lambdaFileName):
  iam_client = boto3.client('iam');

  cur_dir = os.path.dirname(__file__)
  trustFilePath = cur_dir + '/policies/trust_document.txt'
  policyFilePath = cur_dir + '/policies/lambda_dynamo_policy.txt'

  with open(trustFilePath) as trust_role:
    trust_document = trust_role.read()

  with open(policyFilePath) as lambda_policy:
    lambda_document = lambda_policy.read()

  # Creating the IAM role with the specified Trust
  create_role_response = iam_client.create_role(
    RoleName = 'lambda_dynamo_role',
    AssumeRolePolicyDocument = trust_document,
    Description = 'AWS role given to lambda'
  )

  create_policy_response = iam_client.create_policy(
    PolicyName = 'lambda_dynamofullaccess',
    PolicyDocument = lambda_document,
    Description = 'Full dynamoDB access rights policy with logs'
  )

  attach_response = iam_client.attach_role_policy(
    RoleName = 'lambda_dynamo_role',
    PolicyArn = create_policy_response['Policy']['Arn']
  )

  # Download the zip file with the lambda code and save it in the same directory as this script.
  fileNoPy = lambdaFileName.replace(' ', '')[:-3] # Remove the .py extension from the file
  lambdaCodeDir = cur_dir + '/lambda_sourcecode/'
  filePath = lambdaCodeDir + lambdaFileName
  fileNoPyPath = lambdaCodeDir + fileNoPy
  zipfile.ZipFile(fileNoPyPath + '.zip', mode='w').write(filePath, basename(filePath))


  with open(fileNoPyPath + '.zip', mode='rb') as file:   
    filecontent = file.read()

  time.sleep(5)
  while True:
    try:
      lambda_client = boto3.client('lambda')
      create_lambda_response = lambda_client.create_function(
        FunctionName = fileNoPy,
        Runtime = 'python2.7',
        #By appending this script unto create_jitr_lambda.py you do not need to find the role_ARN, as it will already be stored in this object.
        Role = create_role_response['Role']['Arn'],
        Handler = 'iot_to_dynamo.lambda_handler',
        Code = {
          'ZipFile': filecontent
        },
        Description = 'Lambda function for publishing data from IoT to DynamoDB',
      )
    except Exception as e:
      error_code = e.response["Error"]["Code"]
      if error_code == "InvalidParameterValueException":
        print("Created role needs to replicate across AWS...retrying...")
        time.sleep(5)
        continue
      else:
        print(e)
    break