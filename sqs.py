import boto
from datetime import datetime
import simplejson
import inspect
import numpy as np
import uuid

# BOOTSTRAP_SCRIPT = '''#/bin/bash
# apt-get update
# apt-get install -y python-numpy
# 
# python -c "import os
# import json
# import numpy as np
# from datetime import datetime
# 
# import boto
# 
# request_queue = boto.connect_sqs(KEY,SECRET).create_queue('%(REQUEST_QUEUE)s')
# response_queue = boto.connect_sqs(KEY,SECRET).create_queue('%(RESPONSE_QUEUE)s')
# 
# 
# ''' 

global START_SCRIPT
START_SCRIPT = '''#!/bin/bash

apt-get update
apt-get install -y python-numpy python-boto python-simplejson

wget https://raw.githubusercontent.com/wazaahhh/property_game/master/abm.py


python -c "import boto
import simplejson
import urllib

bucketName = 'property_game'
#connect to S3
s3 = boto.connect_s3()
bucket = s3.get_bucket(bucketName)

#download script


#key = bucket.get_key('scripts/abm.py')
#key.get_contents_to_filename('abm.py')

#load script
import abm
PG = abm.property_game()

#connect to SQS and check queue
global sqs
sqs = boto.connect_sqs()

queue = 'property_game'
global q 
q = sqs.create_queue(queue)

while True:
    message = q.read()
    if message is not None:
        msg = simplejson.loads(message.get_body())        
        print msg
        #if msg['perc_filled_sites']==0:
        #    print 'bogus job, skipping'
        #    continue
        #else:
        try:
            PG.simulate(msg,verbose=2,maxHours=11)
            print 'done'
            q.delete_message(message)
        except:
            print 'error'
            q.delete_message(message)
            continue
    else:
        print 'no job left'
        break
"
shutdown -h now
'''


def S3connectBucket(bucketName):
    s3 = boto.connect_s3()
    bucket = s3.get_bucket(bucketName)
    return bucket

queue = 'property_game'

global bucket 
bucket = S3connectBucket(queue)

global sqs
sqs = boto.connect_sqs()

global q 
q = sqs.create_queue(queue)

global ec2
ec2 = boto.connect_ec2()

def postQueueMessage(dic,queue,bucket):
    now = datetime.strftime(datetime.now(),'%Y%m%d%H%M%S')
    dic['queue'] = {'posted':now}
    data = simplejson.dumps(dic)
    key = bucket.new_key("%s/%s_%s.json"%(queue,now,str(uuid.uuid4())))
    key.set_contents_from_string(data)
    message = q.new_message(body=simplejson.dumps({'bucket': bucket.name, 'key': key.name}))
    q.write(message)


def postSimpleSQSMessage(initDic):
    message = q.new_message(body=simplejson.dumps(initDic))
    q.write(message)


def executeSimpleSQSJob():
    message = q.read()
    if message is not None:
        msg = simplejson.loads(message.get_body())        
        print msg
        startECinstance(START_SCRIPT%msg)
        q.delete_message(message)
    else:
        return 0
    
    
def startECinstance(START_SCRIPT,n):
    i=0
    while i<n:
        i+=1
        reservation = ec2.run_instances(image_id='ami-f287459a',
                                    key_name='ec2-sample-key',
                                    instance_type="m3.medium",
                                    placement="us-east-1b",
                                    security_group_ids=["ssh_only"],
                                    instance_initiated_shutdown_behavior='terminate',
                                    instance_profile_name='myinstanceprofile',
                                    user_data = START_SCRIPT)

#initDic = { 'grid_size' : 49, 'iterations' : 200, 'r' : 0.0, 'q' : 0.0 , 'm' : 1 , 's' : 0.0 , 'M':7}
#pDic = {'s': np.linspace(0.00,0.90,21),'perc_filled_sites' : np.linspace(0.0,0.90,21)}
#pDic['s'] = np.array([ 0.01 ,  0.015,  0.02 ,  0.025,  0.03 ,  0.035,  0.045, 0.05, 0.055, 0.06, 0.065])


#def generateJobs(initDic,pDic,n=1):
#    for k  in pDic.keys():
#        print k
#        for value in pDic[k]:
#            i=0
#            while i<n:
#                i+=1
#                initDic[k]=value
                #postSimpleSQSMessage(initDic)
#                print initDic
            

def generateJobs2(n=1,res="low",simulate=False):
    initDic = { 'grid_size' : 49,
               'iterations' : 200,
               'r' : 0.0,
               'q' : 0.0,
               'm' : 1 ,
               's' : 0.0 ,
               'M': 24
               }
    if res=="high":
        random_res = 100.
        #S = np.linspace(0.0,1,21) 
        #S = S + np.random.random(len(S))/100.
        #PFS = np.linspace(0.05,1,20)
        #PFS = PFS + np.random.random(len(PFS))/100.
        
    else:
        random_res = 10.
        #S = np.linspace(0.15,0.16,11)
        S = np.linspace(0.34,0.9,5)
        #S = S + np.random.random(len(S))/10.
        #PFS = np.linspace(0.4,0.6,11)
        
        PFS = np.linspace(0.1,0.9,5)
        #PFS = PFS + np.random.random(len(PFS))/10.
    
    count = 0
    
    for s in S:
        for pfs in PFS:
            i=0
            while i<n:
                i+=1
                if s > 1 or pfs > 1 or s < 0 or pfs <= 0:
                    continue
                else:
                    count += 1
                    initDic['s'] = s + (np.random.random())/random_res
                    initDic['perc_filled_sites' ] = pfs + (np.random.random())/random_res
                    if not simulate:
                        postSimpleSQSMessage(initDic)
                    print count,initDic


def executeMultipleJobs(n=-1):  
    i=0
    while i<n or n==-1:
        i+=1
        check_queue = executeSimpleSQSJob()
        if check_queue==0:
            print "no job in queue"
            break
        

def count(bucket,dir):
    rs = bucket.list(dir)
    i=0
    for k in rs:
        i+=1   
    return i     
#reservation = ec2.run_instances(image_id='ami-f287459a', key_name='ec2-sample-key',instance_type="c3.large",placement="us-east-1b",security_group_ids=["ssh_only"],instance_initiated_shutdown_behavior='terminate',user_data = START_SCRIPT)
        
        
    