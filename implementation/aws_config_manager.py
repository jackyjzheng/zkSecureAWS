import os
import ConfigParser

class AWS_Config_Manager:

  CONFIG_PATH = os.path.expanduser("~") + '/.aws/zymkeyconfig'
  SECTION_NAME = 'aws_arns'

  # sig: ARNs for signature verification
  # db: ARNs for database publishing
  def __init__(self):
    self.config = ConfigParser.ConfigParser()

    self.sig_role_arn = ''
    self.sig_role_name = ''
    self.sig_policy_arn = ''
    self.sig_lambda_arn = ''
    self.sig_topic_rule_arn = ''

    self.db_role_arn = ''
    self.db_role_name = ''
    self.db_policy_arn = ''
    self.db_lambda_arn = ''
    self.db_topic_rule_arn = ''

    self.iot_cert = ''
    self.iot_policy = ''
    self.iot_ca = ''

    self.table_name = ''
    self.sig_subscribed_topic = ''
    self.db_subscribed_topic = ''

    self.initializeConfig()

  def initializeConfig(self):
    fileExists = os.path.exists(AWS_Config_Manager.CONFIG_PATH)
    if (fileExists):
      # Set the class member variables to config variables
      self.config.read(AWS_Config_Manager.CONFIG_PATH)
      self.sig_role_arn = self.config.get(AWS_Config_Manager.SECTION_NAME, 'sig_role_arn')
      self.sig_role_name = self.config.get(AWS_Config_Manager.SECTION_NAME, 'sig_role_name')
      self.sig_policy_arn = self.config.get(AWS_Config_Manager.SECTION_NAME, 'sig_policy_arn')
      self.sig_lambda_arn = self.config.get(AWS_Config_Manager.SECTION_NAME, 'sig_lambda_arn')
      self.sig_topic_rule_arn = self.config.get(AWS_Config_Manager.SECTION_NAME, 'sig_topic_rule_arn')

      self.db_role_arn = self.config.get(AWS_Config_Manager.SECTION_NAME, 'db_role_arn')
      self.db_role_name = self.config.get(AWS_Config_Manager.SECTION_NAME, 'db_role_name')
      self.db_policy_arn = self.config.get(AWS_Config_Manager.SECTION_NAME, 'db_policy_arn')
      self.db_lambda_arn = self.config.get(AWS_Config_Manager.SECTION_NAME, 'db_lambda_arn')
      self.db_topic_rule_arn = self.config.get(AWS_Config_Manager.SECTION_NAME, 'db_topic_rule_arn')

      self.iot_cert = self.config.get(AWS_Config_Manager.SECTION_NAME, 'iot_cert')
      self.iot_policy = self.config.get(AWS_Config_Manager.SECTION_NAME, 'iot_policy')
      self.iot_ca = self.config.get(AWS_Config_Manager.SECTION_NAME, 'iot_ca')


      self.table_name = self.config.get(AWS_Config_Manager.SECTION_NAME, 'table_name')
      self.sig_subscribed_topic = self.config.get(AWS_Config_Manager.SECTION_NAME, 'sig_subscribed_topic')
      self.db_subscribed_topic = self.config.get(AWS_Config_Manager.SECTION_NAME, 'db_subscribed_topic')
    else:
      # If file doesn't exist, set the variables of the config object to empty
      self.config.add_section(AWS_Config_Manager.SECTION_NAME)
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'sig_role_arn', '')
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'sig_role_name', '')
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'sig_policy_arn', '')
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'sig_lambda_arn', '')
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'sig_topic_rule_arn', '')

      self.config.set(AWS_Config_Manager.SECTION_NAME, 'db_role_arn', '')
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'db_role_name', '')
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'db_policy_arn', '')
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'db_lambda_arn', '')
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'db_topic_rule_arn', '')

      self.config.set(AWS_Config_Manager.SECTION_NAME, 'iot_cert', '')
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'iot_policy', '')
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'iot_ca', '')

      self.config.set(AWS_Config_Manager.SECTION_NAME, 'table_name', '')
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'sig_subscribed_topic', '')
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'db_subscribed_topic', '')
      self.saveConfig()

  # Writes the config object in the class to a config file
  def saveConfig(self):
    with open(AWS_Config_Manager.CONFIG_PATH, 'w') as configfile:
      self.config.write(configfile)

  def setRole(self, roleArn, context):
    if context == 'sig':
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'sig_role_arn', roleArn)
      self.sig_role_arn = roleArn
    elif context == 'db':
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'db_role_arn', roleArn)
      self.db_role_arn = roleArn
    self.saveConfig()

  def setRoleName(self, roleName, context):
    if context == 'sig':
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'sig_role_name', roleName)
      self.sig_role_name = roleName
    elif context == 'db':
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'db_role_name', roleName)
      self.db_role_name
    self.saveConfig()

  def setPolicy(self, policyArn, context):
    if context == 'sig':
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'sig_policy_arn', policyArn)
      self.sig_policy_arn = policyArn
    elif context == 'db':
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'db_policy_arn', policyArn)
      self.db_policy_arn = policyArn
    self.saveConfig()

  def setLambda(self, lambdaArn, context):
    if context == 'sig':
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'sig_lambda_arn', lambdaArn)
      self.sig_lambda_arn = lambdaArn
    elif context == 'db':
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'db_lambda_arn', lambdaArn)
      self.db_lambda_arn = lambdaArn
    self.saveConfig()

  def setTopicRule(self, topicRuleArn, context):
    if context == 'sig':
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'sig_topic_rule_arn', topicRuleArn)
      self.sig_topic_rule_arn = topicRuleArn
    elif context == 'db':
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'db_topic_rule_arn', topicRuleArn)
      self.db_topic_rule_arn = topicRuleArn
    self.saveConfig()

  def setIotCert(self, cert):
    self.config.set(AWS_Config_Manager.SECTION_NAME, 'iot_cert', cert)
    self.iot_cert = cert
    self.saveConfig()
  def setIotPolicy(self, policy):
    self.config.set(AWS_Config_Manager.SECTION_NAME, 'iot_policy', policy)
    self.iot_policy = policy
    self.saveConfig()
  def setIotCA(self, CA):
    self.config.set(AWS_Config_Manager.SECTION_NAME, 'iot_ca', CA)
    self.iot_ca = CA
    self.saveConfig()

  def setTable(self, tableName):
    self.config.set(AWS_Config_Manager.SECTION_NAME, 'table_name', tableName)
    self.table_name = tableName
    self.saveConfig()

  def setSubscribedTopic(self, subscribedTopic, context):
    if context == 'sig':
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'sig_subscribed_topic', subscribedTopic)
      self.sig_subscribed_topic = subscribedTopic
    if context == 'db':
      self.config.set(AWS_Config_Manager.SECTION_NAME, 'db_subscribed_topic', subscribedTopic)
      self.db_subscribed_topic = subscribedTopic
    self.saveConfig()
