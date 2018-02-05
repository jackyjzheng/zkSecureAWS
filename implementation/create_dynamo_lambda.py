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
  try:
    create_role_response = iam_client.create_role(
      RoleName = 'lambda_dynamo_role',
      AssumeRolePolicyDocument = trust_document,
      Description = 'AWS role given to lambda'
    )
  except Exception as e:
    error_code = e.response["Error"]["Code"]
    if error_code == "EntityAlreadyExists":
      create_role_response = iam_client.get_role(
        RoleName = 'lambda_dynamo_role'
      )
      print("The role already exists...skipping role creation...")

  try:
    create_policy_response = iam_client.create_policy(
      PolicyName = 'lambda_dynamofullaccess',
      PolicyDocument = lambda_document,
      Description = 'Full dynamoDB access rights policy with logs'
    )
  except Exception as e:
    error_code = e.response["Error"]["Code"]
    if error_code == "EntityAlreadyExists":
      create_policy_response = {}
      create_policy_response['Policy'] = {}
      create_policy_response['Policy']['Arn'] = 'arn:aws:iam::865031943857:policy/lambda_dynamofullaccess'
      print("The policy already exists...skipping policy creation...")

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
      if error_code == 'InvalidParameterValueException':
        print("Created role needs to replicate across AWS...retrying...")
        time.sleep(5)
        continue
      if error_code == 'ResourceConflictException':
        print('Lambda function exists...skipping lambda function creation...')
        create_lambda_response = {}
        create_lambda_response['FunctionArn'] = lambda_client.get_function(
          FunctionName = fileNoPy
        )['Configuration']['FunctionArn']
        break
      else:
        print(e)
    break

  while True:
    try:
      iot_client = boto3.client('iot')
      iot_client.create_topic_rule(
        ruleName = 'publish_to_dynamo',
        topicRulePayload = {
          'sql': 'SELECT * FROM \'Zymkey\'',
          'description': 'Lambda function to forward incoming messages from zymkey to the IoT dynamoDB table',
          'actions': [
            {
              'lambda': {
                'functionArn': create_lambda_response['FunctionArn']
              }
            }
          ]
        }
      )
    except Exception as e:
      error_code = e.response["Error"]["Code"]
      if error_code == 'ResourceAlreadyExistsException':
        print("Topic rule already exists...skipping topic rule creation...")
    create_topic_rule_response = iot_client.get_topic_rule(
      ruleName = 'publish_to_dynamo'
    )

    break

  while True:
    try:
      lambda_client = boto3.client('lambda')
      add_permission_response = lambda_client.add_permission(
        FunctionName = create_lambda_response['FunctionArn'],
        StatementId = '1234567890',
        Action = 'lambda:InvokeFunction',
        Principal = 'iot.amazonaws.com',
        SourceArn = create_topic_rule_response['ruleArn']
      )
    except Exception as e:
      print(e)
    break