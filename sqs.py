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
apt-get install -y python-numpy python-boto python-simplejson ipython
python -c "import boto

import simplejson
bucketName = 'property_game'
#connect to S3
s3 = boto.connect_s3()
bucket = s3.get_bucket(bucketName)

#download script
key = bucket.get_key('scripts/abm.py')
key.get_contents_to_filename('abm.py')

#load script
import abm
PG = abm.property_game()

#connect to SQS and chekc queue
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
        #run simulation
        PG.simulate(msg,verbose=2)
        print 'done'
        q.delete_message(message)
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
                                    instance_type="c3.large",
                                    placement="us-east-1b",
                                    security_group_ids=["ssh_only"],
                                    instance_initiated_shutdown_behavior='terminate',
                                    instance_profile_name='myinstanceprofile',
                                    user_data = START_SCRIPT)

initDic = { 'grid_size' : 49,'iterations' : 200, 'perc_filled_sites' : 0.5,
            'r':0.0,'q':0.0,'m':1,'s':0.05,'M':5}

pDic = {'s': np.linspace(0.1,0.25,7)}

def generateJobs(initDic,pDic,n=1):
    for k  in pDic.keys():
        print k
        for value in pDic[k]:
            i=0
            while i<n:
                i+=1
                initDic[k]=value
                postSimpleSQSMessage(initDic)
                print initDic
            

def executeMultipleJobs(n=-1):  
    i=0
    while i<n or n==-1:
        i+=1
        check_queue = executeSimpleSQSJob()
        if check_queue==0:
            print "no jobs in queue"
            break
        

def count(bucket,dir):
    rs = bucket.list(dir)
    i=0
    for k in rs:
        i+=1   
    return i     
#reservation = ec2.run_instances(image_id='ami-f287459a', key_name='ec2-sample-key',instance_type="c3.large",placement="us-east-1b",security_group_ids=["ssh_only"],instance_initiated_shutdown_behavior='terminate',user_data = START_SCRIPT)
        
        
    