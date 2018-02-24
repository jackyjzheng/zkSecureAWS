from Queue import Queue
from threading import Thread, Semaphore
import sys
import os
import time
import urllib2

import json
import boto3
import hashlib
import binascii
import pycurl
from OpenSSL import SSL
import random
import datetime
import zymkey

failQ = Queue()
qSem = Semaphore()
rwSem = Semaphore()

cur_dir = os.path.dirname(os.path.realpath(__file__))
log_path = os.path.join(cur_dir, 'log.txt')
if not os.path.isfile(log_path):
  f = open(log_path,"w+")
  f.close()

def ZK_AWS_Publish(url, post_field, CA_Path, Cert_Path,):
  #Setting Curl to use zymkey_ssl engine
  c = pycurl.Curl()
  c.setopt(c.SSLENGINE, "zymkey_ssl")
  c.setopt(c.SSLENGINE_DEFAULT, 1L)
  c.setopt(c.SSLVERSION, c.SSLVERSION_TLSv1_2)
  
  #Settings certificates for HTTPS connection
  c.setopt(c.SSLENGINE, "zymkey_ssl")
  c.setopt(c.SSLCERTTYPE, "PEM")
  c.setopt(c.SSLCERT, Cert_Path)
  c.setopt(c.CAINFO, CA_Path)
  
  #setting endpoint and HTTPS type, here it is a POST
  c.setopt(c.URL, url)
  c.setopt(c.POSTFIELDS, post_field)
  
  #Telling Curl to do client and host authentication
  c.setopt(c.SSL_VERIFYPEER, 1)
  c.setopt(c.SSL_VERIFYHOST, 2)
  
  #Turn on Verbose output and set key as placeholder, not actually a real file.
  c.setopt(c.VERBOSE, 0)
  c.setopt(c.SSLKEYTYPE, "ENG") 
  c.setopt(c.SSLKEY, "nonzymkey.key")
  c.setopt(c.TIMEOUT, 5)
  try:
    c.perform()
    return 0
  except Exception as e:
    return -1

# Checking if we can connect to one of Google's IP
def internet_on():
    try:
        urllib2.urlopen('http://216.58.192.142', timeout=2)
        return True
    except urllib2.URLError as err: 
        return False
    except Exception as e:
      print('no')

# This thread would check for any data failed to publish from the failQ queue and write it to a log file
def checkFailQueue():
  global internetOn
  while True:
    qSem.acquire()
    if failQ.qsize() > 100 or (internetOn and (failQ.qsize() is not 0)):
      print('queue reached ' + str(failQ.qsize()))
      rwSem.acquire()
      with open(log_path, "a") as myfile:
        num = 0
        while failQ.qsize() > 0:
          data = failQ.get()
          myfile.write('---NEW ITEM---\n' + str(data) + '\n')
          num += 1
        print('wrote ' + str(num) + ' items from queue')
      rwSem.release() 
    qSem.release()

# This thread will check the log file for any failed events and retry sending them 
def retrySend():
  global internetOn
  while True:
    rwSem.acquire()
    if internetOn: # Connection is alive
      if not os.stat(log_path).st_size == 0: # There is data that needs to reupload
        numPublish = 1
        with open(log_path) as f:
          next(f) # Skip the first ---NEW ITEM--- tag
          dataBuilder = ''
          json_data = ''
          for line in f:
            if '---NEW ITEM---' not in line:
              dataBuilder += line
            else:
              json_data = json.dumps(dataBuilder)
              print('RETRY ITEM ' + str(numPublish) + ' HAS BEEN BUILT AND CONTAINS ' + str(json_data))
              if ZK_AWS_Publish(url=AWS_ENDPOINT, post_field=json_data, CA_Path='/home/pi/Zymkey-AWS-Kit/bash_scripts/CA_files/zk_ca.pem', Cert_Path='/home/pi/Zymkey-AWS-Kit/zymkey.crt') is not -1:
                print('\tRETRY PUBLISH item ' + str(numPublish) + ' from retry')
              else:
                print('Couldnt publish ' + str(numPublish) + ' added to queue')
                failQ.put(json_data)
              numPublish += 1
              dataBuilder = '' # Reset the dataBuilder to empty string
          # Print out the very last item in the file
          json_data = json.dumps(dataBuilder)
          print('RETRY ITEM ' + str(numPublish) + ' HAS BEEN BUILT AND CONTAINS ' + str(json_data))
          if ZK_AWS_Publish(url=AWS_ENDPOINT, post_field=json_data, CA_Path='/home/pi/Zymkey-AWS-Kit/bash_scripts/CA_files/zk_ca.pem', Cert_Path='/home/pi/Zymkey-AWS-Kit/zymkey.crt') is not -1:
            print('\tLAST RETRY PUBLISH item ' + str(numPublish) + ' from retry')
          else:
            print('Couldnt publish ' + str(numPublish) + ' added to queue')
            failQ.put(json_data)
        f = open(log_path, 'w+') # Create a new blank log.txt for new logging
        f.close()
    rwSem.release()
    time.sleep(3) # Retrying the publish isn't too essential to do in quick time

failThread = Thread(target = checkFailQueue)
retryThread = Thread(target = retrySend)

failThread.daemon = True
retryThread.daemon = True

internetOn = internet_on()
failThread.start()
retryThread.start()

# Data generation setup
boto3client = boto3.client('iot')
topic = "Zymkey"
AWS_ENDPOINT = "https://" + str(boto3client.describe_endpoint()['endpointAddress']) + ":8443/topics/" + topic + "?qos=1"    
device_id = "1"
ip = "192.168.12.28"

try:
  while True:
    # Generate the sample data to try to send
    timestamp = datetime.datetime.now()
    temp_data = {"tempF": random.randint(70,100), "tempC" : random.randint(35, 50)}
    encrypted_data = zymkey.client.lock(bytearray(json.dumps(temp_data)))
    signature = zymkey.client.sign(encrypted_data)
    data = {"ip": ip, "signature": binascii.hexlify(signature), "encryptedData": binascii.hexlify(encrypted_data), "tempData": temp_data}
    post_field = {"deviceId": device_id, "timestamp": str(timestamp), "data": data}
    json_data = json.dumps(post_field)

    if not internet_on():
      internetOn = False
      qSem.acquire()
      print('No connection detected...putting the data into offline storage')
      failQ.put(json_data)
      qSem.release()
    else:
      internetOn = True
      if ZK_AWS_Publish(url=AWS_ENDPOINT, post_field=json_data, CA_Path='/home/pi/Zymkey-AWS-Kit/bash_scripts/CA_files/zk_ca.pem', Cert_Path='/home/pi/Zymkey-AWS-Kit/zymkey.crt') is -1:
        failQ.put(json_data)
      print('\tREGULAR PUBLISH: Leftover q size ' + str(failQ.qsize()))
except KeyboardInterrupt:
  print('Exiting...')
  sys.exit()
