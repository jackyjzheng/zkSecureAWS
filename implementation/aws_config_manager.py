import os
import ConfigParser

class AWS_Config_Manager:

  CONFIG_PATH = os.path.expanduser("~") + '/.aws/zymkeyconfig'
  SECTION_NAME = 'aws_arns'

  def __init__(self):
    self.config = ConfigParser.ConfigParser()
    self.role_arn = ''
    self.policy_arn = ''
    self.lambda_arn = ''
    self.table_name = ''
    self.initializeConfig()

  def __del__(self):
    self.saveConfig()

  def initializeConfig(self):
    fileExists = os.path.exists(AWS_Config_Manager.CONFIG_PATH)
    if (fileExists):
      self.config.read(AWS_Config_Manager.CONFIG_PATH)
      self.role_arn = self.config.get(AWS_Config_Manager.SECTION_NAME, 'role_arn')
      self.policy_arn = self.config.get(AWS_Config_Manager.SECTION_NAME, 'policy_arn')
      self.lambda_arn = self.config.get(AWS_Config_Manager.SECTION_NAME, 'lambda_arn')
      self.table_name = self.config.get(AWS_Config_Manager.SECTION_NAME, 'table_name')
    else:
      self.config.add_section(AWS_Config_Manager.SECTION_NAME)
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'role_arn', '')
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'policy_arn', '')
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'lambda_arn', '')
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'table_name', '')
      self.saveConfig()

  def saveConfig(self):
    with open(AWS_Config_Manager.CONFIG_PATH, 'w') as configfile:
      self.config.write(configfile)

  def setRole(self, roleArn):
    self.config.set(AWS_Config_Manager.SECTION_NAME, 'role_arn', roleArn)
    self.role_arn = roleArn

  def setPolicy(self, policyArn):
    self.config.set(AWS_Config_Manager.SECTION_NAME, 'policy_arn', policyArn)
    self.policy_arn = policyArn

  def setLambda(self, lambdaArn):
    self.config.set(AWS_Config_Manager.SECTION_NAME, 'lambda_arn', lambdaArn)
    self.lambda_arn = lambdaArn

  def setTable(self, tableName):
    self.config.set(AWS_Config_Manager.SECTION_NAME, 'table_name', tableName)
    self.table_name = tableName


