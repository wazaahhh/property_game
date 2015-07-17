
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

def prepareXYZ(parDic):
    resultDic = loadResults(parDic)
    dic = resultArray(resultDic,['perc_filled_sites','s','cooperators'])
    #print len(dic['s'])
    x = np.array(dic['perc_filled_sites'])
    y = np.array(dic['s'])
    z = np.array(dic['cooperators'])

    xi = np.linspace(min(x), max(x),100)
    yi = np.linspace(min(y), max(y),100)

    #xi = np.linspace(0.1, 0.65)
    #yi = np.linspace(0.1, 0.5)

    X, Y = np.meshgrid(xi, yi)
    Z = griddata(np.array(zip(*[x, y])), z, (X, Y),method="linear")
    Z[Z<0.001]=0
    Z[Z>1]=1
    Z[np.isnan(Z)]=0
    
    return {'X':X,'Y':Y,'Z':Z}

def export2plotly(parDic):
    
    dicXYZ = prepareXYZ(parDic)
    
    data = Data([
        Surface(
            z = dicXYZ['Z'],
            x = dicXYZ['X'],
            y = dicXYZ['Y'],
            name='trace0',
            colorscale=[[0, 'rgb(0,0,131)'], [0.125, 'rgb(0,60,170)'], [0.375, 'rgb(5,255,255)'], [0.625, 'rgb(255,255,0)'], [0.875, 'rgb(250,0,0)'], [1, 'rgb(128,0,0)']]
        )
    ])
    layout = Layout(
        title='ppGame_M%.2f_r%.2f_q%.2f_m%.2f'%(parDic['M'],parDic['r'],parDic['q'],parDic['m']),
        autosize = False,
        width = 1500,
        height = 900,
        margin=Margin(
            l=50,
            r=50,
            b=100,
            t=100,
            pad=4
        ),
        scene=Scene(
            xaxis=XAxis(
                range=[0, 1],
                domain=[1,0],
                title = '',
                #titlefont = Font(size = 18),
                tickfont = Font(size = 14),
                nticks=10,
                gridcolor='rgb(255, 255, 255)',
                gridwidth=2,
                zerolinecolor='rgb(255, 255, 255)',
                zerolinewidth=2
            ),
            yaxis=YAxis(
                title = '',
                #titlefont = Font(size = 18),
                tickfont = Font(size = 14),
                nticks=10,
                gridcolor='rgb(255, 255, 255)',
                gridwidth=2,
                zerolinecolor='rgb(255, 255, 255)',
                zerolinewidth=2
            ),
            zaxis=ZAxis(
                range=[0, 1],
                domain=[0, 1],
                autorange=False,
                title = '',
                #titlefont = Font(size = 18),
                tickfont = Font(size = 14),
                nticks=10,
                gridcolor='rgb(255, 255, 255)',
                gridwidth=2,
                zerolinecolor='rgb(255, 255, 255)',
                zerolinewidth=2
            ),
            bgcolor='rgb(244, 244, 248)'
        )
    )
    fig = Figure(data=data, layout=layout)
    plot_url = py.plot(fig)
    return plot_url


def phase_transition(parDic,dRange=[0.4,0.6]):
    resultDic = loadResults(parDic)
    dic = resultArray(resultDic,['perc_filled_sites','s','cooperators'])
    #print dic.keys()
    d = np.array(dic['perc_filled_sites'])
    c = np.array(dic['cooperators'])
    s = np.array(dic['s'])

    cond = (d >= dRange[0]) * ( d < dRange[1])
    
    s = s[cond]
    c = c[cond]
    d = d[cond]
    o = np.argsort(s)
    
    return {'s' : s[o],'c' : c[o],'d':d[o]}
    
  

def plotTimeSeries(simulDic,density=[0.46,0.54],violations=[0.155,0.16]):

    K = searchKeys(simulDic)
    l = len(K)
    K2 = []
    D = []
    V= []

    for k in K:
        d = float(re.findall("_filled(.*?)_",k.name)[0])
        v = float(re.findall("_s(.*?)_",k.name)[0])

        if (d < density[0]) or (d > density[1]):
            continue
        elif (v < violations[0]) or (v > violations[1]):
            continue
        else:
            K2 = np.append(K2,k)
            D = np.append(D,d)
            V = np.append(V,v)

    o = np.lexsort([D,V])
    K2 = K2[o]
    V = V[o]
    D = D[o]

    print len(K2)

    pl.figure(1,(15,12))
    matplotlib.rcParams.update({'font.size': 22,'legend.fontsize': 14})

    for i,k in enumerate(K2):
        print i,k.name
        simulResults = simplejson.loads(k.get_contents_as_string())
        c = simulResults['output']['cooperation']['c']
        pl.plot(c,ls="-",lw=2 - float(i)/len(K2)*1.8,label="%s: s=%.4f, d=%.2f"%(i,V[i],D[i]))


    title = "M = %s, %.4f < d < %.4f, %.4f < s < %.4f"%(simulDic['M'],density[0],density[1],violations[0],violations[1])
    pl.plot(np.arange(200),np.zeros([200])+0.5,'k-')
    pl.legend(loc=0)
    pl.xlabel("Iterations")
    pl.ylabel("Cooperation Level")
    pl.xlim(xmax=300)
    pl.title(title)
    #pl.figure(2)
    #pl.plot(np.diff(c))
    pl.savefig(rootDir + "figures/tseries_%s.eps"%title)
    


def pickRandomInitConfig(parDic):
    print "blah"

    
'''
def routineLoop():
    #Just a loop to make a few simulations
    initDic = { 'grid_size' : 49,'iterations' : 200, 'perc_filled_sites' : .9,'r':0.0,'q':0,'m':1,'s':0.0,'M':3}
    initDicKey = "initial_conditions/initGrid/initGrid_simul200_grid49_filled0.9_M3.json"
    for i in range(10):
        print i+1, "/10 (M=3)"
        dic = PG.simulate(initDic,uploadToS3=True,verbose=2,loadStrategies=initDicKey)
'''


#if __name__ == '__main__':
    
    #parDic = {'iterations' : 200,'grid_size' : 49, 'perc_filled_sites' : 0.3,
    #        'r':0.05,'q':0.05,'m':1.0,'M':3}

    #redoAll()