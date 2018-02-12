import zipfile
import boto3
import os
import time
from os.path import basename
from aws_config_manager import AWS_Config_Manager

def createLambdaFunction(lambdaFileName):
  iam_client = boto3.client('iam');
  aws_config = AWS_Config_Manager()

  cur_dir = os.path.dirname(__file__)
  trustFilePath = cur_dir + '/policies/trust_document.txt'
  policyFilePath = cur_dir + '/policies/lambda_dynamo_policy.txt'

  with open(trustFilePath) as trust_role:
    trust_document = trust_role.read()

  with open(policyFilePath) as lambda_policy:
    lambda_document = lambda_policy.read()

  # Creating the IAM role with the specified Trust
  try:
    roleName = 'lambda_dynamo_role'
    create_role_response = iam_client.create_role(
      RoleName = roleName,
      AssumeRolePolicyDocument = trust_document,
      Description = 'AWS role given to lambda'
    )
  except Exception as e:
    error_code = e.response["Error"]["Code"]
    if error_code == "EntityAlreadyExists":
      create_role_response = iam_client.get_role(
        RoleName = roleName
      )
      print("Rolep already exists...skipping role creation and updating role arn in /.aws/zymkeyconfig...")
  finally:
    aws_config.setRole(create_role_response['Role']['Arn'])
    aws_config.setRoleName(roleName)

  # Creating the policy
  try:
    policyName = 'lambda_dynamofullaccess'
    create_policy_response = iam_client.create_policy(
      PolicyName = policyName,
      PolicyDocument = lambda_document,
      Description = 'Full dynamoDB access rights policy with logs'
    )
    aws_config.setPolicy(create_policy_response['Policy']['Arn'])
  except Exception as e:
    error_code = e.response["Error"]["Code"]
    if error_code == "EntityAlreadyExists":
      print("Policy already exists...skipping policy creation and updating policy arn in /.aws/zymkeyconfig...")

  attach_response = iam_client.attach_role_policy(
    RoleName = aws_config.role_name,
    PolicyArn = aws_config.policy_arn
  )

  # Download the zip file with the lambda code and save it in the same directory as this script.
  fileNoPy = lambdaFileName.replace(' ', '')[:-3] # Remove the .py extension from the file
  lambdaCodeDir = cur_dir + '/lambda_sourcecode/'
  filePath = lambdaCodeDir + lambdaFileName
  fileNoPyPath = lambdaCodeDir + fileNoPy
  zipfile.ZipFile(fileNoPyPath + '.zip', mode='w').write(filePath, basename(filePath))


  with open(fileNoPyPath + '.zip', mode='rb') as file:   
    filecontent = file.read()

  create_lambda_response = {}
  while True:
    try:
      lambda_client = boto3.client('lambda')
      create_lambda_response = lambda_client.create_function(
        FunctionName = fileNoPy,
        Runtime = 'python2.7',
        #By appending this script unto create_jitr_lambda.py you do not need to find the role_ARN, as it will already be stored in this object.
        Role = aws_config.role_arn,
        Handler = 'iot_to_dynamo.lambda_handler',
        Code = {
          'ZipFile': filecontent
        },
        Description = 'Lambda function for publishing data from IoT to DynamoDB',
      )
      break
    except Exception as e:
      error_code = e.response["Error"]["Code"]
      if error_code == 'InvalidParameterValueException':
        print("Created role needs to replicate across AWS...retrying...")
        time.sleep(5)
        continue
      if error_code == 'ResourceConflictException':
        print('Lambda function already exists...skipping lambda function creation and updating lambda arn in /.aws/zymkeyconfig')
        create_lambda_response['FunctionArn'] = lambda_client.get_function(
          FunctionName = fileNoPy
        )['Configuration']['FunctionArn']
        break
      else:
        print(e)
  aws_config.setLambda(create_lambda_response['FunctionArn'])

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
                'functionArn': aws_config.lambda_arn
              }
            }
          ]
        }
      )
    except Exception as e:
      error_code = e.response["Error"]["Code"]
      if error_code == 'ResourceAlreadyExistsException':
        print('Topic rule already exists...skipping topic rule creation and updating topic rule arn in /.aws/zymkeyconfig...')

    create_topic_rule_response = iot_client.get_topic_rule(
      ruleName = 'publish_to_dynamo'
    )
    aws_config.setTopicRule(create_topic_rule_response['ruleArn'])

    break

  while True:
    try:
      lambda_client = boto3.client('lambda')
      add_permission_response = lambda_client.add_permission(
        FunctionName = aws_config.lambda_arn,
        StatementId = '1234567890',
        Action = 'lambda:InvokeFunction',
        Principal = 'iot.amazonaws.com',
        SourceArn = aws_config.topic_rule_arn
      )
    except Exception as e:
      error_code = e.response["Error"]["Code"]
      if error_code == 'ResourceConflictException':
        print('Lambda trigger already exists...skipping lambda trigger creation...')
    break

  print('Successful setup')