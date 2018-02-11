import os
import ConfigParser

class AWS_Config_Manager:

  CONFIG_PATH = os.path.expanduser("~") + '/.aws/zymkeyconfig.ini'

  def __init__(self):
    self.config = ConfigParser.ConfigParser()
    self.role_arn = ''
    self.policy_arn = ''
    self.lambda_arn = ''
    self.table_name = ''
    self.initializeConfig()

  def initializeConfig(self):
    awsSectionName = 'aws_arns'
    isExisting = os.path.exists(AWS_Config_Manager.CONFIG_PATH)
    if (isExisting):
      pass
      #self.config.read(CONFIG_PATH)
    else:
      self.config.add_section(awsSectionName)
      self.config.set(awsSectionName, 'role_arn', '')
      self.config.set(awsSectionName, 'policy_arn', '')
      self.config.set(awsSectionName, 'lambda_arn', '')
      self.config.set(awsSectionName, 'table_name', '')
      with open(AWS_Config_Manager.CONFIG_PATH, 'w') as configfile:
        self.config.write(configfile)