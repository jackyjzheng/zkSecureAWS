from Queue import Queue
from threading import Thread, Lock, Semaphore
import sys
import os
import time # For Testing with "putting data in queue"
import calendar
import urllib2

failQ = Queue()
mutex = Semaphore()
rw = Semaphore()

cur_dir = os.path.dirname(os.path.realpath(__file__))
log_path = os.path.join(cur_dir, 'log.txt')
if not os.path.isfile(log_path):
  f = open(log_path,"w+")
  f.close()

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
    mutex.acquire()
    if failQ.qsize() > 100 or (internetOn and (failQ.qsize() is not 0)):
      print('queue reached ' + str(failQ.qsize()))
      rw.acquire()
      with open(log_path, "a") as myfile:
        num = 0
        while failQ.qsize() > 0:
          data = failQ.get()
          myfile.write('---NEW ITEM---\n' + str(data) + '\n')
          num += 1
        print('wrote ' + str(num) + ' items from queue')
      rw.release() 
    mutex.release()

# This thread will check the log file for any failed events and retry sending them 

def retrySend():
  global internetOn
  while True:
    rw.acquire()
    if internetOn:
      if not os.stat(log_path).st_size == 0:
        with open(log_path) as f:
          content = f.readlines() # Read the lines from file
          print('RETRYING ' + str(content)) # Do something with the lines of text
          f = open(log_path, 'w+') # Create a new blank log.txt for new logging
          f.close() 
    rw.release()
    time.sleep(3)

failThread = Thread(target = checkFailQueue)
retryThread = Thread(target = retrySend)

failThread.daemon = True
retryThread.daemon = True

internetOn = internet_on()
failThread.start()
retryThread.start()

count = 0
try:
  while True:
    if not internet_on():
      internetOn = False
      mutex.acquire()
      print('Adding ' + str(calendar.timegm(time.gmtime())) + ' to queue from main loop')
      failQ.put(count)
      count += 1
      mutex.release()
      time.sleep(.02)
    else:
      internetOn = True
      print('Real time ' + str(calendar.timegm(time.gmtime())) + ' to queue from main loop')
      print('Leftover q ' + str(failQ.qsize()))
except KeyboardInterrupt:
  print('Exiting...')
  sys.exit()
