### The Zymkey Secure AWS Project
---
We present an application to connect to Amazon Web Services through a more secure paradigm, using a un-exportable and un-readable private key stored in a hardware security module (HSM) for the Raspberry Pi, [Zymkey]().

Furthermore our application will demonstrate the storage of encrypted and authenticated sensor data on Amazon's NoSQL DynamoDB. All data published will be encrypted with an AES-256 key and digitally signed by an ECDSA-Prime256 key stored on Zymkey. Data will be verified by Zymkey's corresponding public key through an AWS Lambda function before either being stored in database.

Additional features include the storage of data encrypted on the filesystem when internet connection goes down, to be re-published when connection comes back up, data will remain in time-order once republished to the database.

### Application Overview

Our application automates the setup of AWS infrastructure and allows a user to automatically publish encrypted and authenticated data to AWS servers through a secure pipeline with Zymkey straight out of the box. Specifically client authentication is done through HTTPS, with the client presenting an X.509 certificate presenting Zymkey's public ECDSA key, and then verifying to the server that they have the corresponding private key. Since Zymkey stores the  private key outside of the file system and is un-readable and un-exportable, and only works when bound to as specific Raspberry Pi, secure paradigm and shit.

All certificates are signed by a Certificate Authority of the user's choice. The AWS endpoint will only accept Certificates and Certificate Authorities registered on the user's AWS account, this setup is automated, all the user needs to do is point to their Certificate Authority files.

The ECDSA key used for establishing a secure connection with AWS is also used to digitally sign temperature data. Since HTTPS authentication is itself done through the client signing an arbitrary message from the server this makes sense. When the Zymkey certificate is registered on the user's AWS account, it's signing public key is also registered. Furthermore data sent to the client's AWS endpoint will be authenticated against this public key, and dropped if authentication fails. 

Data is stored encrypted in a DynamoDB database indexed by client generated timestamps. Data that fails signature authentication is quarintined in a seperation partition of the database, to allow for examination in the future.

Our application grabs temperature data from multiple temperature sensors attached to the Raspberry Pi, the [DS18B20 OneWire probes](https://learn.adafruit.com/adafruits-raspberry-pi-lesson-11-ds18b20-temperature-sensing/hardware). A timestamp is generated for the data and  it is encrypted via. AES and signed via ECDSA, with the result being hex-encoded. Data is then assembled in a json format, before it is sent to AWS Servers.

Finally our applications allows the storage of data encrypted on disk when connection drops. Once internet connection is restored data is read from disk and republished. This part of the sensor application is multi-threaded and a more technical description can be found in the technical documentation.

### Dependencies
---
Depdencies can be installed via a bash script.

* [boto3](https://boto3.readthedocs.io/en/latest/) - [Version: 1.5.36]
* [pycurl](http://pycurl.io/) - [Version: 7.43.0.1] 
* [OpenSSL](https://www.openssl.org/) - [Version: 1.0.1t]
* libcurl4-openssl-dev, libssl-dev
* [pyOpenSSL](https://pyopenssl.org/en/stable/) - [Version: 0.13.1]
* [jsrsasign](https://kjur.github.io/jsrsasign/) - [Version: 8.06]
* [python-edsa](https://github.com/warner/python-ecdsa) - [Version: 0.13]
---
### Setup
(1) Bind the Zymkey to your Raspberry Pi. We recommend doing a temporary development binding to setup up your workflow properly before doing a permanent binding. Follow the instructions [here]() to get all more information, can be done simply by running the following command.
```
 curl -G https://s3.amazonaws.com/zk-sw-repo/install_zk_sw.sh | sudo bash
```
(2) Install the pre-requisite software by running install_dependencies.sh in bash_scripts/
```
bash install_dependencies.sh
```
(3) Setup your AWS account by following these instructions:
(4) Run main.py and follow the instructions making sure to copy in your AWS credentials.
```
python main.py
```
(5) Begin publishing data securely with your certificates! Try out the publish_data.py script.
```
python publish_data.py
```
### Application Architecture
