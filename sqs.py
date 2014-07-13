import boto
from datetime import datetime
import simplejson
import inspect
import numpy as np
import uuid

BOOTSTRAP_SCRIPT = '''#/bin/bash
apt-get update
apt-get install -y python-numpy

python -c "import os
import json
import numpy as np
from datetime import datetime

import boto

request_queue = boto.connect_sqs(KEY,SECRET).create_queue('%(REQUEST_QUEUE)s')
response_queue = boto.connect_sqs(KEY,SECRET).create_queue('%(RESPONSE_QUEUE)s')


''' 


def S3connectBucket(bucketName):
    s3 = boto.connect_s3()
    bucket = s3.get_bucket(bucketName)
    return bucket

queue = 'sqs_pgame'

global bucket 
bucket = S3connectBucket(queue)

global sqs
sqs = boto.connect_sqs()


global q
q = sqs.create_queue(queue)


def postQueueMessage(dic,queue,bucket):
    now = datetime.strftime(datetime.now(),'%Y%m%d%H%M%S')
    dic['queue'] = {'posted':now}
    data = simplejson.dumps(dic)
    key = bucket.new_key("%s/%s_%s.json"%(queue,now,str(uuid.uuid4())))
    key.set_contents_from_string(data)
    message = q.new_message(body=simplejson.dumps({'bucket': bucket.name, 'key': key.name}))
    q.write(message)

def generateJobs(r=0,q=0,m=0,s=0,M=5):
    frame = inspect.currentframe()
    args, _, _, values = inspect.getargvalues(frame)
    argDic={args[i]:values[ix] for i,ix in enumerate(args)}
    
    dic = argDic.copy()
    
    for k  in argDic.keys():
        if hasattr(argDic[k], "__len__"):
            for i,ix in enumerate(argDic[k]):
                dic[k]=ix
                print dic
                postQueueMessage(dic,queue,bucket)
    
    
def executeJobs(multiple=True):  
    while True:
        message = q.read()
        if message is not None:   # if it is continue reading until you get a message
            msg_data = simplejson.loads(message.get_body())
            key = boto.connect_s3().get_bucket(msg_data['bucket']).get_key(msg_data['key'])
            dic = simplejson.loads(key.get_contents_as_string())   
            dic['queue']['executed'] = datetime.strftime(datetime.now(),'%Y%m%d%H%M%S')
            print dic
            key.set_contents_from_string(simplejson.dumps(dic))
            q.delete_message(message)
            
            if multiple==False:
                break
        else:
            break
        
        
#reservation = ec2.run_instances(image_id='ami-f287459a', key_name='ec2-sample-key',instance_type="c3.large",placement="us-east-1b",security_group_ids=["ssh_only"],instance_initiated_shutdown_behavior='terminate',user_data = START_SCRIPT)
        
        
    