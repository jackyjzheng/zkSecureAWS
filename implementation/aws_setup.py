import zipfile
import boto3
import os
import time
import sys
from os.path import basename
from aws_config_manager import AWS_Config_Manager
from botocore.exceptions import ClientError

class AWS_Setup:

  def __init__(self):
    self.aws_config = AWS_Config_Manager()
    self.cur_dir = os.path.dirname(__file__)

  def dbSetup(self):
    context = 'db'
    self.createTable('IoT')
    if self.createRole('zymkey_role', 'trust_document.txt', context) == -1:
      sys.exit()
    if self.createPolicy('lambda_dynamofullaccess', 'lambda_dynamo_policy.txt', context) == -1:
      sys.exit()
    self.attachRolePolicy(context)
    if self.createLambdaFunction('iot_to_dynamo', 'iot_to_dynamo.py', 'lambda_handler', 'python', context) == -1:
      sys.exit()
    self.createTopicRule('publish_to_dynamo', 'Zymkey', context)
    self.createLambdaTrigger('1234567890', context)
    print('Successful setup! Publish data to topic \'' + self.aws_config.subscribed_topic + '\' to get started!')

  def sigSetup(self):
    context = 'sig'
    if self.createRole('lambdaModifyRole', 'trust_document.txt', context) == -1: 
      sys.exit()
    if self.createPolicy('lambdaModifyPolicy', 'lambdaModifyPolicy.txt', context) == -1:
      sys.exit()                       
    self.attachRolePolicy(context)
    if self.createLambdaFunction('setPublicKey', 'pubKeyLambda.js', 'lambda_handler', 'nodejs', context) == -1:
      sys.exit()
    self.createTopicRule('getPubKeyfromCert', 'certID', context)
    self.createLambdaTrigger('1337', context)
    print('Succesful for the modifyLambda function.')

  def createTable(self, tableName):
    print('---Creating DynamoDB table...this may take up to 20 seconds---')
    try:
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
      table.meta.client.get_waiter('table_exists').wait(TableName=tableName)
    except ClientError as e:
      error_code = e.response["Error"]["Code"]
      if error_code == "ResourceInUseException":
        print('Table already exists...skipping table creation and updating table name in /.aws/zymkeyconfig...')
    finally:
      self.aws_config.setTable(tableName)

  # roleName is the name of the role to be created
  # trustFile located under the policies folder in the repo (ie. trust_document.txt)
  # returns -1 for error
  def createRole(self, roleName, trustFile, context):
    print('---Creating role---')
    trustFilePath = os.path.join(self.cur_dir, 'policies', trustFile)
    if not os.path.isfile(trustFilePath):
      print('Trust file could not be found at ' + trustFilePath)
      print('FAILURE...exiting script...')
      return -1

    iam_client = boto3.client('iam')
    with open(trustFilePath) as trust_role:
      trust_document = trust_role.read()

    # Creating the IAM role with the specified Trust
    try:
      create_role_response = iam_client.create_role(
        RoleName = roleName,
        AssumeRolePolicyDocument = trust_document,
        Description = 'AWS role given to lambda'
      )
    except ClientError as e:
      error_code = e.response['Error']['Code']
      if error_code == 'EntityAlreadyExists':
        create_role_response = iam_client.get_role(
          RoleName = roleName
        )
        print('Role already exists...skipping role creation and updating role arn in ~/.aws/zymkeyconfig...')
      else:
        print(e)
    except Exception as e:
      print(e)
    finally:
      self.aws_config.setRole(create_role_response['Role']['Arn'], context)
      self.aws_config.setRoleName(roleName, context)

  # policyName is the name of the policy to be created
  # policyFile located under the policies folder in the repo (ie. lambda_dynamo_policy.txt)
  # returns -1 for error, 0 for success
  def createPolicy(self, policyName, policyFile, context):
    print('---Creating policy---')
    policyFilePath = os.path.join(self.cur_dir, 'policies', policyFile)
    if not os.path.isfile(policyFilePath):
      print('Policy file could not be found at ' + policyFilePath)
      print('FAILURE...exiting script...')
      return -1

    iam_client = boto3.client('iam')

    with open(policyFilePath) as lambda_policy:
      lambda_document = lambda_policy.read()

    # Creating the policy
    try:
      create_policy_response = iam_client.create_policy(
        PolicyName = policyName,
        PolicyDocument = lambda_document,
        Description = 'Full dynamoDB access rights policy with logs'
      )
      self.aws_config.setPolicy(create_policy_response['Policy']['Arn'], context)
    except ClientError as e:
      error_code = e.response['Error']['Code']
      if error_code == 'EntityAlreadyExists':
        print('Policy already exists...skipping policy creation...using the policy_arn from ~/.aws/zymkeyconfig')
        if self.aws_config.sig_policy_arn == '' or self.aws_config.db_policy_arn == '':
          print('Cannot get the existing policy_arn from ~/.aws/zymkeyconfig... Manually update ~/.aws/zymkeyconfig yourself')
          print('FAILURE...exiting script...')
          return -1 # Policy exists in AWS, but not specified in the zymkeyconfig
        else:
          return 0 # Policy exists in AWS, and is correctly specified in zymkeyconfig so we continue
      else:
        print(e)
    except Exception as e:
      print(e)

  def attachRolePolicy(self, context):
    print('---Attaching the role to the policy---')
    iam_client = boto3.client('iam')
    roleName = ''
    policyArn = ''
    if context == 'sig':
      roleName = self.aws_config.sig_role_name
      policyArn = self.aws_config.sig_policy_arn
    elif context == 'db':
      roleName = self.aws_config.db_role_name
      policyArn = self.aws_config.db_policy_arn

    attach_response = iam_client.attach_role_policy(
      RoleName = roleName,
      PolicyArn = policyArn
    )

  # functionName is the unique name to call this lambda function on AWS
  # lambdaFileName is the name of the lambda function code with extension (ie. iot_to_dynamo.py)
  # lambdaFunctionHandler is name of function to be ran inside the file, lambdaFileName (ie. lambda_handler)
  # returns -1 for error
  def createLambdaFunction(self, functionName, lambdaFileName, lambdaFunctionHandler, codeLanguage, context):
    print('---Creating lambda function---')
    # Download the zip file with the lambda code and save it in the same directory as this script.
    fileNoPy = lambdaFileName.replace(' ', '')[:-3] # Remove the .py extension from the file
    lambdaCodeDir = os.path.join(self.cur_dir, 'lambda_sourcecode')
    filePath = os.path.join(lambdaCodeDir, lambdaFileName)
    if not os.path.isfile(filePath):
      print('\'' + lambdaFileName + '\' could not be found at \'' + filePath + '\'')
      print('FAILURE...exiting script...')
      return -1

    fileNoPyPath = os.path.join(lambdaCodeDir, fileNoPy) # Where we will create the zip of the lamdba source code
    
    if not os.path.isfile(fileNoPyPath + '.zip'):
      zipfile.ZipFile(fileNoPyPath + '.zip', mode='w').write(filePath, basename(filePath))

    with open(fileNoPyPath + '.zip', mode='rb') as file:   
      filecontent = file.read()

    lambda_runtime = ''
    create_lambda_response = {}
    role = ''

    if codeLanguage == 'python':
      lambda_runtime = 'python2.7'
    elif codeLanguage == 'nodejs':
      lambda_runtime = 'nodejs6.10'
    if context == 'sig':
      role = self.aws_config.sig_role_arn
    elif context == 'db':
      role = self.aws_config.db_role_arn


    while True:
      try:
        lambda_client = boto3.client('lambda')
        create_lambda_response = lambda_client.create_function(
          FunctionName = functionName,
          Runtime = lambda_runtime,
          Role = role,
          Handler = fileNoPy + '.' + lambdaFunctionHandler,
          Code = {
            'ZipFile': filecontent
          },
          Description = 'Lambda function for publishing data from IoT to DynamoDB',
        )
        break
      except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'InvalidParameterValueException':
          print('Created role needs to replicate across AWS...retrying...')
          time.sleep(5)
          continue
        elif error_code == 'ResourceConflictException':
          print('Lambda function already exists...skipping lambda function creation and updating lambda arn in ~/.aws/zymkeyconfig')
          create_lambda_response['FunctionArn'] = lambda_client.get_function(
            FunctionName = functionName
          )['Configuration']['FunctionArn']
          break
        else:
          print('An error occured...lambda_arn has been unset in ~/.aws/zymkeyconfig')
          print(e)
          break
      except Exception as e:
        print(e)
    self.aws_config.setLambda(create_lambda_response['FunctionArn'], context)

  # topicRuleName is name of topic rule to be created
  # subscribedTopic is name of the IoT topic where data will be published
  def createTopicRule(self, topicRuleName, subscribedTopic, context):
    print('---Creating topic rule---')
    lambdaArn = ''
    if context == 'sig':
      lambdaArn = self.aws_config.sig_lambda_arn
    elif context == 'db':
      lambdaArn = self.aws_config.db_lambda_arn
    try:
      iot_client = boto3.client('iot')
      iot_client.create_topic_rule(
        ruleName = topicRuleName,
        topicRulePayload = {
          'sql': 'SELECT * FROM \'' + subscribedTopic + '\'',
          'description': 'Lambda function to forward incoming messages from zymkey to the IoT dynamoDB table',
          'actions': [
            {
              'lambda': {
                'functionArn': lambdaArn
              }
            }
          ]
        }
      )
    except ClientError as e:
      error_code = e.response['Error']['Code']
      if error_code == 'ResourceAlreadyExistsException':
        print('Topic rule already exists...skipping topic rule creation and updating topic rule arn in ~/.aws/zymkeyconfig...')
      else:
        print(e)
    except Exception as e:
      print(e)

    # Topic rule response set outside the try except block because create_topic_rule from AWS API returns nothing
    # so we must try to create the rule then check the topicRuleName argument to see what its ARN is
    create_topic_rule_response = iot_client.get_topic_rule(
      ruleName = topicRuleName
    )
    self.aws_config.setTopicRule(create_topic_rule_response['ruleArn'], context)
    self.aws_config.setSubscribedTopic(subscribedTopic)

  # statementId is an arbitrary identifier for the trigger
  def createLambdaTrigger(self, statementId, context):
    print('---Creating lambda trigger---')
    functionName = ''
    sourceArn = ''
    if context == 'sig':
      functionName = self.aws_config.sig_lambda_arn
      sourceArn = self.aws_config.sig_topic_rule_arn
    elif context == 'db':
      functionName = self.aws_config.db_lambda_arn
      sourceArn = self.aws_config.db_topic_rule_arn
    try:
      lambda_client = boto3.client('lambda')
      add_permission_response = lambda_client.add_permission(
        FunctionName = functionName,
        StatementId = statementId,
        Action = 'lambda:InvokeFunction',
        Principal = 'iot.amazonaws.com',
        SourceArn = sourceArn
      )
    except ClientError as e:
      error_code = e.response['Error']['Code']
      if error_code == 'ResourceConflictException':
        print('Lambda trigger already exists...skipping lambda trigger creation...')
      else:
        print(e)
    except Exception as e:
      print(e)
