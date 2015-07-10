
from matplotlib import use, get_backend
if 'Agg' != get_backend().title(): 
    use('Agg')

'''Main Modules'''
from scipy import stats as S
import boto
import json,simplejson
import re
import numpy as np
import pylab as pl
import os

bucketName = "property_game"
s3 = boto.connect_s3()
global bucket
bucket = s3.get_bucket(bucketName)

rootDir = "/home/ubuntu/github/property_game/"

global folder
folder = "results/json/"


def searchKeys(parDic):
    keys = bucket.list(prefix=folder)
    
    parameters = sorted(parDic.iterkeys())
    #print parameters

    
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
        #print k.name
        iter,grid,fill,time,r,q,m,s,M = re.findall(pattern,k.name)[0]
        
        tmpDic = {'iterations' : int(iter),'grid_size' : int(grid), 'perc_filled_sites' : float(fill),
            'r': float(r),'q': float(q),'m': float(m),'s': float(s),'M': int(M)}
        
        kValues = []
        parValues = []
        
        for p in parameters:
            kValues.append(tmpDic[p])
            parValues.append(parDic[p])
        
        if kValues==parValues:
            #print iter,grid,fill,time,r,q,m,s,M
            K.append(k)
            
    return K

def loadResults(parDic,save=True,overwrite=False):
    keyname = "results/results_%s.json"%"_".join("%s%s"%ix for ix in parDic.items())
    
    ''' try loading results'''
    key = bucket.get_key(keyname)
    if key != None and overwrite == False:
        #print "loading result dictionary from S3"
        resultDic = simplejson.loads(key.get_contents_as_string())
    else:
        print "dictionary not found on S3; processing data; please wait"
        K = searchKeys(parDic)
        resultDic = {}
    
        for i,k in enumerate(K):
            print i,len(K),k
            Jk = simplejson.loads(k.get_contents_as_string())
            #print k
            dic = Jk['input']
            dic.pop('strategy_init')
            
            dic['cooperators'] = Jk['output']['cooperators']
            dic['filled_sites'] = Jk['output']['filled_sites']
            dic['MCS'] = Jk['output']['iterations']
            resultDic[k.name] = dic
            
        if save:
            output = bucket.new_key(keyname)
            output.set_contents_from_string(simplejson.dumps(resultDic))
            
    return resultDic


def resultArray(resultDic,variables):
    dic = {}
    for v in variables:
        #print v
        for values in resultDic.values():
            try:
                dic[v].append(values[v])
            except:
                dic[v] = [values[v]]

    return dic


def twoDimPlot(results,varName):
    x = []
    y = []
    
    par = results.values()[0]['input'].copy()
    par.pop(varName)
    
    for i,ix in enumerate(results.values()):
        #print ix['input'][varName],ix['output']['cooperators']
        x = np.append(x,ix['input'][varName])
        y = np.append(y,ix['output']['cooperators'])
        
    
    c = x<1
    x = x[c]
    y = y[c]
    
    o = np.argsort(x)
    x = x[o]
    y = y[o]  
    pl.close("all")
    pl.figure(1,(12,12))
    pl.plot(x,y,'o-')
    pl.xlabel("s")
    pl.ylabel("final %age of cooperators")
    print y
    c = y < 0.005
    try:
        xmax = max(x[c][3],0.25)
    except:
        xmax = max(x[c][-1],0.25)
        
    pl.xlim(xmax=xmax)
    pl.savefig(rootDir+"figures/plot_%s.png"%"_".join("%s%s"%ix for ix in par.items()))
    
    return np.array(x),np.array(y)

#def plot(parDic):
#    K = searchKeys(parDic)
#    resultDic = loadResults(K)
#    twoDimPlot(resultDic,'s')
    
def redoAll():
    plots = os.listdir("figures")
    list = ['grid_size','M','m','perc_filled_sites','q','r','iterations']

    for p in plots:
        pattern = "plot_grid_size(.*?)_M(.*?)_m(.*?)_perc_filled_sites(.*?)_q(.*?)_r(.*?)_iterations(.*?).png"
        regex = map(float,re.findall(pattern,p)[0])
        dic = dict(zip(list, regex))
        print dic        
        plot(dic)

def trajectories(resultDic):
    pl.close("all")
    pl.figure(1,(12,10))
    
    '''order by s'''
    sValues = []
    for i,ix in enumerate(resultDic.values()):
        sValues.append(ix['input']['s'])
        
    order = np.argsort(sValues)
    
    
    
    for i,ix in enumerate(order):
        ix = resultDic.values()[ix]
        s = ix['input']['s']
        #if s < 0.15:
        #    continue
        
        x = ix['output']['cooperation']['iteration']
        y = ix['output']['cooperation']['c']
        pl.plot(x,y,label=str(s))
        print i,order[i],s,ix['output']['cooperation']['c'][-1],ix['output']['cooperators']
    
    pl.legend(prop={'size':11})
    pl.xlim(xmax = 600000)
    pl.xlabel("iterations")
    pl.ylabel("cooperation level")
    pl.show()


#if __name__ == '__main__':
    
    #parDic = {'iterations' : 200,'grid_size' : 49, 'perc_filled_sites' : 0.3,
    #        'r':0.05,'q':0.05,'m':1.0,'M':3}

    #redoAll()