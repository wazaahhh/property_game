'''Main Modules'''
from scipy import stats as S
import boto
import json,simplejson
import re
import numpy as np

bucketName = "property_game"
s3 = boto.connect_s3()
global bucket
bucket = s3.get_bucket(bucketName)


#parDic = {'iterations' : 200,'grid_size' : 49, 'perc_filled_sites' : 0.5,'r':0.0,'q':0.0,'m':1.0,'s':0.05,'M':5}

parDic = {'iterations' : 200,'grid_size' : 49, 'perc_filled_sites' : 0.5,
            'r':0.0,'q':0.0,'m':1.0,'M':5}

folder = "results/json/"

def searchKeys(parDic):
    keys = bucket.list(prefix=folder)
    
    parameters = sorted(parDic.iterkeys())
    print parameters

    
    minT='20100808060402'
    
    '''
    strFormat = "results/json/simul%s_grid%s_filled%.2f_%s_r%.2f_q%.2f_m%.2f_s%.2f_M%s.json"%(parDic['iterations'],
      parDic['grid_size'],
      parDic['perc_filled_sites'],
      minT,
      parDic['r'],
      parDic['q'],
      parDic['m'],
      parDic['s'],
      parDic['M'])
    '''
    
    pattern = "results/json/simul(.*?)_grid(.*?)_filled(.*?)_(.*?)_r(.*?)_q(.*?)_m(.*?)_s(.*?)_M(.*?).json"
    
    
    K = []
    
    for k in keys:
        iter,grid,fill,time,r,q,m,s,M = re.findall(pattern,k.name)[0]
        
        tmpDic = {'iterations' : int(iter),'grid_size' : int(grid), 'perc_filled_sites' : float(fill),
            'r': float(r),'q': float(q),'m': float(m),'s': float(s),'M': int(M)}
        
        kValues = []
        parValues = []
        
        for p in parameters:
            kValues.append(tmpDic[p])
            parValues.append(parDic[p])
        
        #print k
        #print parValues
        #print kValues
        #print '\n'
        
        #print kdic
        
        if kValues==parValues:
            print iter,grid,fill,time,r,q,m,s,M
            K.append(k)
            
    return K

def loadResults(K):
    for k in K:
        J = simplejson.loads(k.get_contents_as_string())
        print J.keys()
   
   