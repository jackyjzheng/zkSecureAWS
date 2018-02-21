import zipfile
import boto3
import os
import time
from os.path import basename
from aws_config_manager import AWS_Config_Manager
from botocore.exceptions import ClientError

class AWS_Lambda_Setup:

  def __init__(self):
    self.aws_config = AWS_Config_Manager()
    self.cur_dir = os.path.dirname(__file__)

  def defaultLambdaSetup(self):
    if self.createRole('zymkey_role', 'trust_document.txt') == -1:
      return -1
    if self.createPolicy('lambda_dynamofullaccess', 'lambda_dynamo_policy.txt') == -1:
      return -1
    self.attachRolePolicy()
    if self.createLambdaFunction('iot_to_dynamo', 'iot_to_dynamo.py', 'lambda_handler') == -1:
      return -1
    self.createTopicRule('publish_to_dynamo', 'Zymkey')
    self.createLambdaTrigger('1234567890')
    print('Successful setup! Publish data to topic \'' + self.aws_config.subscribed_topic + '\' to get started!')

  # roleName is the name of the role to be created
  # trustFile located under the policies folder in the repo (ie. trust_document.txt)
  # returns -1 for error
  def createRole(self, roleName, trustFile):
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
    except Exception as e:
      print(e)
    finally:
      self.aws_config.setRole(create_role_response['Role']['Arn'])
      self.aws_config.setRoleName(roleName)

  # policyName is the name of the policy to be created
  # policyFile located under the policies folder in the repo (ie. lambda_dynamo_policy.txt)
  # returns -1 for error, 0 for success
  def createPolicy(self, policyName, policyFile):
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
      self.aws_config.setPolicy(create_policy_response['Policy']['Arn'])
    except ClientError as e:
      error_code = e.response['Error']['Code']
      if error_code == 'EntityAlreadyExists':
        print('Policy already exists...skipping policy creation...using the policy_arn from ~/.aws/zymkeyconfig')
        if self.aws_config.policy_arn is '':
          print('Cannot get the existing policy_arn from ~/.aws/zymkeyconfig... Check ~/.aws/zymkeyconfig')
          print('FAILURE...exiting script...')
          return -1 # Policy exists in AWS, but not specified in the zymkeyconfig
        else:
          return 0 # Policy exists in AWS, and is correctly specified in zymkeyconfig so we continue
    except Exception as e:
      print(e)

  def attachRolePolicy(self):
    print('---Attaching the role to the policy---')
    iam_client = boto3.client('iam')
    attach_response = iam_client.attach_role_policy(
      RoleName = self.aws_config.role_name,
      PolicyArn = self.aws_config.policy_arn
    )

  # functionName is the unique name to call this lambda function on AWS
  # lambdaFileName is the name of the lambda function code with extension (ie. iot_to_dynamo.py)
  # lambdaFunctionHandler is name of function to be ran inside the file, lambdaFileName (ie. lambda_handler)
  # returns -1 for error
  def createLambdaFunction(self, functionName, lambdaFileName, lambdaFunctionHandler):
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
    zipfile.ZipFile(fileNoPyPath + '.zip', mode='w').write(filePath, basename(filePath))


    with open(fileNoPyPath + '.zip', mode='rb') as file:   
      filecontent = file.read()

    create_lambda_response = {}
    while True:
      try:
        lambda_client = boto3.client('lambda')
        create_lambda_response = lambda_client.create_function(
          FunctionName = functionName,
          Runtime = 'python2.7',
          Role = self.aws_config.role_arn,
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
        if error_code == 'ResourceConflictException':
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
    self.aws_config.setLambda(create_lambda_response['FunctionArn'])

  # topicRuleName is name of topic rule to be created
  # subscribedTopic is name of the IoT topic where data will be published
  def createTopicRule(self, topicRuleName, subscribedTopic):
    print('---Creating topic rule---')
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
                'functionArn': self.aws_config.lambda_arn
              }
            }
          ]
        }
      )
    except ClientError as e:
      error_code = e.response['Error']['Code']
      if error_code == 'ResourceAlreadyExistsException':
        print('Topic rule already exists...skipping topic rule creation and updating topic rule arn in ~/.aws/zymkeyconfig...')
    except Exception as e:
      print(e)

    # Topic rule response set outside the try except block because create_topic_rule from AWS API returns nothing
    # so we must try to create the rule then check the topicRuleName argument to see what its ARN is
    create_topic_rule_response = iot_client.get_topic_rule(
      ruleName = topicRuleName
    )
    self.aws_config.setTopicRule(create_topic_rule_response['ruleArn'])
    self.aws_config.setSubscribedTopic(subscribedTopic)

  # statementId is an arbitrary identifier for the trigger
  def createLambdaTrigger(self, statementId):
    print('---Creating lambda trigger---')
    try:
      lambda_client = boto3.client('lambda')
      add_permission_response = lambda_client.add_permission(
        FunctionName = self.aws_config.lambda_arn,
        StatementId = statementId,
        Action = 'lambda:InvokeFunction',
        Principal = 'iot.amazonaws.com',
        SourceArn = self.aws_config.topic_rule_arn
      )
    except ClientError as e:
      error_code = e.response['Error']['Code']
      if error_code == 'ResourceConflictException':
        print('Lambda trigger already exists...skipping lambda trigger creation...')
    except Exception as e:
      print(e)