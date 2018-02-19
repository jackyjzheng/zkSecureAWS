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

  def defaultLambdaSetup():
    pass

  # trustFile and policyFile will be looked for under the policies folder in the repo
  # Takes in name of the .py file (ie. trust_document.txt)
  # returns -1 for error
  def createRole(trustFile, policyFile):
    trustFilePath = os.path.join(self.cur_dir, 'policies', trustFile)
    if (!os.path.isfile(trustFilePath)):
      print('Trust file could not be found at ' + trustFilePath)
      return -1

    iam_client = boto3.client('iam')
    with open(trustFilePath) as trust_role:
      trust_document = trust_role.read()

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
        print("Role already exists...skipping role creation and updating role arn in /.aws/zymkeyconfig...")
    finally:
      self.aws_config.setRole(create_role_response['Role']['Arn'])
      self.aws_config.setRoleName(roleName)

  def createPolicy(policyFile):
    policyFilePath = os.path.join(self.cur_dir, 'policies', policyFile)
    if (!os.path.isfile(policyFilePath)):
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
        print("Policy already exists...skipping policy creation. Unable to automatically update /.aws/zymkeyconfig... Manually input the policy_arn")

  def attachRolePolicy():
    attach_response = iam_client.attach_role_policy(
      RoleName = self.aws_config.role_name,
      PolicyArn = self.aws_config.policy_arn
    )

  # default lambdaFileName is iot_to_dynamo.py
  # default lambdaFunctionHandler is lambda_handler
  def createLambdaFunction(lambdaFileName, lambdaFunctionHandler):
    # Download the zip file with the lambda code and save it in the same directory as this script.
    fileNoPy = lambdaFileName.replace(' ', '')[:-3] # Remove the .py extension from the file
    lambdaCodeDir = os.path.join(self.cur_dir, 'lambda_sourcecode')
    filePath = os.path.join(lambdaCodeDir, lambdaFileName)
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
          Handler = fileNoPy + '.' + lambdaFunctionHandler
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
    self.aws_config.setLambda(create_lambda_response['FunctionArn'])

  # default ruleName is publish_to_dynamo
  # default subscribedTopic is Zymkey
  def createTopicRule(topicRuleName, subscribedTopic):
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
  def createLambdaTrigger(statementId)
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