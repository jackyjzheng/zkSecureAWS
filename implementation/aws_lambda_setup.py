import zipfile
import boto3
import os
import time
from os.path import basename
from aws_config_manager import AWS_Config_Manager

class AWS_Lambda_Setup:

  def __init__(self):
    self.aws_config = AWS_Config_Manager()
    self.cur_dir = os.getcwd()

  def defaultLambdaSetup(self):
    self.createRole('zymkey_role', 'trust_document.txt', 'lambda_dynamo_policy.txt')
    if self.createPolicy('lambda_dynamo_policy.txt') == -1:
      return -1
    self.attachRolePolicy()
    self.createLambdaFunction('iot_to_dynamo.py', 'lambda_handler')
    self.createTopicRule('publish_to_dynamo', 'Zymkey')
    self.createLambdaTrigger('1234567890')
    print('Successful setup, publish data to topic \'Zymkey\' to get started!')

  # roleName is default zymkey_role
  # trustFile and policyFile will be looked for under the policies folder in the repo
  # Takes in name of the .py file (ie. trust_document.txt)
  # returns -1 for error
  def createRole(self, roleName, trustFile, policyFile):
    print('Creating role...')
    trustFilePath = os.path.join(self.cur_dir, 'policies', trustFile)
    if not os.path.isfile(trustFilePath):
      print('Trust file could not be found at ' + trustFilePath)
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
    except Exception as e:
      error_code = e.response["Error"]["Code"]
      if error_code == "EntityAlreadyExists":
        create_role_response = iam_client.get_role(
          RoleName = roleName
        )
        print("Role already exists...skipping role creation and updating role arn in /.aws/zymkeyconfig...")
    finally:
      self.aws_config.setRole(create_role_response['Role']['Arn'])
      self.aws_config.setRoleName(roleName)

  def createPolicy(self, policyFile):
    print('Creating policy...')
    policyFilePath = os.path.join(self.cur_dir, 'policies', policyFile)
    if not os.path.isfile(policyFilePath):
      print('Policy file could not be found at ' + policyFilePath)
      return -1

    iam_client = boto3.client('iam')

    with open(policyFilePath) as lambda_policy:
      lambda_document = lambda_policy.read()

    # Creating the policy
    try:
      policyName = 'lambda_dynamofullaccess'
      create_policy_response = iam_client.create_policy(
        PolicyName = policyName,
        PolicyDocument = lambda_document,
        Description = 'Full dynamoDB access rights policy with logs'
      )
      self.aws_config.setPolicy(create_policy_response['Policy']['Arn'])
    except Exception as e:
      error_code = e.response["Error"]["Code"]
      if error_code == "EntityAlreadyExists":
        print('Policy already exists...skipping policy creation. Unable to automatically update /.aws/zymkeyconfig... Manually input the policy_arn')
        print('Cannot parse policy_arn from /.aws/zymkeyconfig... Must manually input into the config file')
        print('FAILURE...exiting script...')
        return -1

  def attachRolePolicy(self):
    print('Attaching the role to the policy...')
    iam_client = boto3.client('iam')
    attach_response = iam_client.attach_role_policy(
      RoleName = self.aws_config.role_name,
      PolicyArn = self.aws_config.policy_arn
    )

  # default lambdaFileName is iot_to_dynamo.py
  # default lambdaFunctionHandler is lambda_handler
  def createLambdaFunction(self, lambdaFileName, lambdaFunctionHandler):
    print('Creating lambda function')
    # Download the zip file with the lambda code and save it in the same directory as this script.
    fileNoPy = lambdaFileName.replace(' ', '')[:-3] # Remove the .py extension from the file
    lambdaCodeDir = os.path.join(self.cur_dir, 'lambda_sourcecode')
    filePath = os.path.join(lambdaCodeDir, lambdaFileName)
    if not os.path.isfile(filePath):
      print('\'' + lambdaFileName + '\' could not be found at \'' + filePath + '\'')
      return -1

    fileNoPyPath = os.path.join(lambdaCodeDir, fileNoPy)
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
          Role = self.aws_config.role_arn,
          Handler = fileNoPy + '.' + lambdaFunctionHandler,
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
          print('An error occured...lambda_arn has been unset in /.aws/zymkeyconfig')
          print(e)
          break
    self.aws_config.setLambda(create_lambda_response['FunctionArn'])

  # default topicRuleName is publish_to_dynamo
  # default subscribedTopic is Zymkey
  def createTopicRule(self, topicRuleName, subscribedTopic):
    print('Creating topic rule...')
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
    except Exception as e:
      error_code = e.response["Error"]["Code"]
      if error_code == 'ResourceAlreadyExistsException':
        print('Topic rule already exists...skipping topic rule creation and updating topic rule arn in /.aws/zymkeyconfig...')

    # Topic rule response set outside the try except block because create_topic_rule from AWS API returns nothing
    # so we must try to create the rule then check the topicRuleName argument to see what its ARN is
    create_topic_rule_response = iot_client.get_topic_rule(
      ruleName = topicRuleName
    )
    self.aws_config.setTopicRule(create_topic_rule_response['ruleArn'])

  # statementId is an arbitrary identifier for the trigger
  def createLambdaTrigger(self, statementId):
    print('Creating lambda trigger...')
    try:
      lambda_client = boto3.client('lambda')
      add_permission_response = lambda_client.add_permission(
        FunctionName = self.aws_config.lambda_arn,
        StatementId = statementId,
        Action = 'lambda:InvokeFunction',
        Principal = 'iot.amazonaws.com',
        SourceArn = self.aws_config.topic_rule_arn
      )
    except Exception as e:
      error_code = e.response["Error"]["Code"]
      if error_code == 'ResourceConflictException':
        print('Lambda trigger already exists...skipping lambda trigger creation...')