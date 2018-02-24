from implementation.aws_setup import AWS_Setup
import os

aws_credentials_path = os.path.expanduser("~") + '/.aws/credentials'
if not os.path.exists(aws_credentials_path):
    aws_key_id = raw_input("Please enter your AWS Key id: ")
    aws_secret_key = raw_input("Please enter your AWS secret key: ")
    aws_region = raw_input("Please enter your AWS Region: ")
    with open(aws_credentials_path, 'w') as f:
        f.write("[default]\n")
        f.write("aws_access_key_id = " + aws_key_id + "\n")
        f.write("aws_secret_access_key = " + aws_secret_key + "\n")
        f.write("region=" + aws_region)

aws_lambdaModify_setup = AWS_Setup()
aws_lambdaModify_setup.modifyLambdaSetup()

#awsSetup = AWS_Setup()
#awsSetup.defaultSetup()