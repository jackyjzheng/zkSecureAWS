---
### The Zymkey Secure AWS Project
---
We present an application to connect to Amazon Web Services through a more secure paradigm, using a un-exportable and un-readable private key stored in a hardware security module (HSM) for the Raspberry Pi, [Zymkey](https://www.zymbit.com/), to establish an HTTPS connection.

Furthermore our application will demonstrate the storage of encrypted and authenticated sensor data on Amazon's NoSQL DynamoDB. All data published will be encrypted with an AES-256 key and digitally signed by an ECDSA-prime256v1 key stored on Zymkey. Data will be verified by Zymkey's corresponding public key through an AWS lambda function before being moved to the database. All incorrectly signed data will be moved to a seperate quarantined database.

Additional features include the storage of data encrypted on the filesystem when internet connection goes down, to be re-published when connection comes back up: data will remain in time-order once republished to the database.

The entire application is setup by one python script. All that is required is for the user to install Zymkey, setup their AWS account and run the script. Furthermore once the script has finished the user is free to publish arbitrary data to AWS IoT securely and can create their own AWS application utilizing the secure pipeline setup.

## Table of Contents
1. [Application Overview](#app_overview)
2. [Dependencies](#dependencies)
3. [Setup](#setup)
4. [Application Architecture](#app_architecture)
5. [License](#license)

### <a name="app_overview"/> Application Overview 
---
**Our application automates the setup of AWS infrastructure and allows a user to automatically publish encrypted and authenticated data to AWS servers through a cryptographically secure pipeline with Zymkey straight out of the box**. Specifically client authentication is done through HTTPS, with the client presenting an X.509 certificate presenting Zymkey's public ECDSA key, and then verifying to the server that they have the corresponding private key. Since Zymkey stores the  private key outside of the file system and is un-readable and un-exportable, and only works when bound to a specific Raspberry Pi, it is much more secure than the conventional way of connecting to AWS via a readable private key on the file system.

All certificates are signed by a Certificate Authority of the user's choice. The AWS endpoint will only accept Certificates and Certificate Authorities registered on the user's AWS account, this setup is automated, all the user needs to do is point to their Certificate Authority files.

The ECDSA key used for establishing a secure connection with AWS is also used to digitally sign temperature data. Since HTTPS authentication is itself done through the client signing an arbitrary message from the server this makes sense. When the Zymkey certificate is registered on the user's AWS account, it's signing public key is also registered. Furthermore data sent to the client's AWS endpoint will be authenticated against this public key, and dropped if authentication fails. 

Data is stored encrypted in a DynamoDB database indexed by client generated timestamps. Data that fails signature authentication is quarintined in a seperation partition of the database, to allow for examination in the future.

Our application grabs temperature data from multiple temperature sensors attached to the Raspberry Pi, the [DS18B20 OneWire probes](https://learn.adafruit.com/adafruits-raspberry-pi-lesson-11-ds18b20-temperature-sensing/hardware). A timestamp is generated for the data and  it is encrypted via. AES and signed via ECDSA, with the result being hex-encoded. Data is then assembled in a json format, before it is sent to AWS Servers.

Finally our applications allows the storage of data encrypted on disk when connection drops. Once internet connection is restored data is read from disk and republished. This part of the sensor application is multi-threaded and a more technical description can be found in the technical documentation.

We will continue to update the repo as we polish the project, in-depth technical documentation covering the entire architecture of this application will be published shortly.

### <a name="dependencies"/> Dependencies 
---
Depdencies and their versions are listed here. Most is installed upon setting up Zymkey, pycurl and pyOpenSSL currently need to be installed manually.

* [boto3](https://boto3.readthedocs.io/en/latest/) - [Version: 1.5.36]
* [pycurl](http://pycurl.io/) - [Version: 7.43.0.1] 
* [OpenSSL](https://www.openssl.org/) - [Version: 1.0.1t]
* [pyOpenSSL](https://pyopenssl.org/en/stable/) - [Version: 0.13.1]

The following software are used by our Signature Verification lambda functions. They do not need to be installed on your system, but are packaged with our code and will be deployed to your AWS account.

* [jsrsasign](https://kjur.github.io/jsrsasign/) - [Version: 8.06]
* [python-edsa](https://github.com/warner/python-ecdsa) - [Version: 0.13]

### <a name="setup"/> Setup
---
#### Zymkey Binding
Since we are using the Zymkey as a cryptographic HSM, we need to set it up on your Raspberry Pi. We recommend doing a temporary development binding to begin with and allow you to set up your workflow properly before doing a permanent binding. Look at the following post [here](https://community.zymbit.com/t/getting-started-with-zymkey-4i/202/6) to get a more information. However, from a fresh install of Raspbian Jessie, it boils down to 2 simple steps.

(1) The first step is to configure the state of the I2C bus to “ON”.  This can be done by logging in to your pi and running:
```
sudo raspi-config
Select Interfacing Options -> I2C
Would you like the ARM I2C interface to be enabled ? select (Yes) then enter, and enter.
Select Finish
```
Your I2C bus is now configured and ready to talk to the Zymkey. 

(2) The next step is to install the pre-requisite Zymkey software and to do developer binding. This can be done by running the following command:
```
 curl -G https://s3.amazonaws.com/zk-sw-repo/install_zk_sw.sh | sudo bash
```
(3) Ensure your Zymkey is bound properly by running the following command, and getting a valid response, if you get any errors visit the [Zymbit community page](https://community.zymbit.com/) for help.
```python
python
import zymkey
zymkey.client.sign('Hello World!')
```
#### Connecting your AWS Account
We now need to configure your AWS account so that our python scripts, specifically the boto3 module, is able to access your account and set up the application. **Note that the current setup requires you to create an IAM user with Admin credentials**, with credentials stored on your file system. These credentials are planned to be locked by Zymkey's AES key after use, and we will give the option of deleting them after they are used, but we are working on creating a User with more restrictive access privileges in the future. Feel free to delete the User and Credentials manually after application setup if you wish.

**---Instructions---**
(1) Sign in to your **AWS console** here: https://aws.amazon.com/console/
(2) From the **AWS Console**, choose the **IAM** service.
(3) From **IAM**, go to **Users** and then **Add User**.
(4) Give the User an appropriate name, and give it **Programmatic Access**. Choose to **Attach Existing Policies Directly** and give it **AdministratorAccess**.
(5) **Save the Access key ID and Secret access key**, it will need to be input into the script. If you wish to save your credentials yourself you can create a credentials file in **~/.aws/credentials**.

#### Running the Script
Now we will setup the application by running the python script **main.py**. The script will ask for **two things**: the path to your **CA certificate** and **CA key file**, and the credentials for your AWS account. Note that if you don't have a CA you can generate a test CA by running the script.

(1) Install the boto3 module with the following command:
```
sudo pip install boto3
```
(2) Install python-openssl
```
sudo apt-get install python-openssl
```
(3) Next we clone the github repo:
```
git clone https://github.com/jackyjzheng/zkSecureAWS.git
```
(4) We want change into the appropriate directory, which is the main directory where the scripts are located:
```
cd zkSecureAWS
```
---
**Optional Step:**
If you don't have a Certificate Authority or want to generate one for testing you can run the follow bash script:
```
bash bash_scripts/gen_example_ca.sh
```
Note that the CA is then stored in bash_scripts/CA_files. There certificate is stored as zk_ca.pem and the key as zk_ca.key.

---
(5) Create the following directory if it doesn't already exist:
```
mkdir ~/.aws
```
(6) Run main.py and follow the instructions making sure to copy in your AWS credentials. **Make sure your time and date are correct!**
```
sudo sntp -s time.google.com
python main.py
```
(7) If everything is sucessful you can begin publishing data securely with your certificates! Try out the publish_data.py script. You will find the data published to your AWS IoT gateway under the topic /Zymkey. It is then routed to a lambda function which will handle signature verification, and stored in your DynamoDB database.
```
python publish_data.py
```
(8) Now try the publish_bad_data.py script. The data will still make it to the IoT gateway, but will not pass signature verification. As a result it will be published to the quarantined database.
### <a name="app_architecture"/> Application Architecture
---
### <a name="license"/> License 
---
