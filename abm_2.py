import numpy as np
from random import choice,randrange, shuffle
import time
from datetime import datetime
import json,simplejson
import boto

import abmlib
dreload(abmlib)
from abmlib import *
from aws_connect import *

global bucketName
bucketName = "property_game"
s3 = boto.connect_s3()

global bucket 
bucket = s3.get_bucket(bucketName)

global initDic

def loadParameters():
    '''search for the set of parameters on S3'''
    print initDic['M']


def coopLevel(strategies):
    coop = np.array(strategies.values())
    cooperators = float(len(coop[coop==1]))/len(coop[coop>=0])
    defectors = float(len(coop[coop==0]))/len(coop[coop>=0])
    empty = float(len(coop[coop<0]))/len(coop[coop>=0])
    return {'c' : cooperators,'d' : defectors,'e':empty}


def initialize_grid(size,perc_filled_sites):
    '''initialize grid with an equi-probable set of each strategy specified in STRATEGY_SET, 
    among all non-exmpty sites (defined by perc_filled_sites)'''

    STRATEGY_SET = {'C':1,'D':0}

    l = size**2

    shuffle_grid = np.arange(l)        
    shuffle(shuffle_grid)
    
    if perc_filled_sites < 1:
        ''' select randomly sites out of grid in proportion of perc_filled_site'''
        max = round(perc_filled_sites*l+np.random.rand()-0.5)
        subgrid = shuffle_grid[:max]
        rest = shuffle_grid[max:]
    else:
        subgrid = np.arange(0,l)
        rest = []

    shuffle(subgrid)
             
    '''assign strategies'''
    strategies = {}
    
    for i,ix in enumerate(subgrid):
        strategies[ix]=choice(STRATEGY_SET.values())
    
    for i,ix in enumerate(rest):
        strategies[ix]=-1
        
    return strategies


def make_grid(strategies):
    '''Turns a strategy dictionary into a command line viewable grid'''
    values  = []
    for key in sorted(strategies):
        values.append(strategies[key])
    
    grid = np.array(values).reshape([grid_size,grid_size])    
    return grid


def crop_grid(site,strategies,M):
    ''' specifies a region of interest, for large grids'''
    
    grid = make_grid(strategies)
    grid_size = len(grid)
    
    if site < 0 or site > grid_size**2-1:
        print "error site out of bounds"

    index_x = np.arange(site/grid_size-M,site/grid_size+M+1)%grid_size
    index_y = np.arange(site%grid_size-M,site%grid_size+M+1)%grid_size
    
    index = np.meshgrid(index_x,index_y)
    
    print grid[index].T
    
    
    
'''Basic Evolutionary Game Theory Tools'''       
def find_neighbors(site,strategies,non_empty_sites=True):
    '''find 4 nearest neighbors'''
    l = len(strategies.keys())
    size=np.sqrt(l)
    nghbs = np.array([site-1,site+1,site-size,site+size])%l
    
    if non_empty_sites==True:
        n = []
        for i,ix in enumerate(nghbs):
            if strategies[ix] > -1:
                n.append(ix)
        
        nghbs = np.array(n)
    
    return nghbs


def pay_off(site,strategies):
    '''find overall pay-off for site, i.e.,
    play simultaneously with all neighbors'''
    
    
    '''find neighbors (non empty sites)'''  
    if isinstance(site,int) or isinstance(site,float):
        nghbs_1 = find_neighbors(site,strategies)
    elif len(site) == 2:
        nghbs_1 = find_neighbors(site[0],strategies)
        
    poff = []

    for i,ix in enumerate(nghbs_1):
        p1 = prisoners_dilemma(site,ix,strategies)[0]
        poff = np.append(poff,p1)
        
    return np.sum(poff)


def play_with_random_neighbor(site,strategies):
    '''play with a random neighbor'''
    
    poff = {'o_site' : site, 'o_pay_off' : pay_off(site, strategies)}
    
    
    '''find neighbors (non empty sites)'''        
    nghbs_1 = find_neighbors(site,strategies)
    
    '''randomly select a neighbor (non empty site)'''
    if len(nghbs_1)>0:
        site_2 = choice(nghbs_1)

    else:
        #print "no neighbor"
        return poff
    
    poff['site_2'] = site_2
    poff['site2_pay_off'] = pay_off(site_2, strategies) 
                     
    return poff


def  play_with_all_neighbors(site,strategies):
    '''play with all four nearest neighbors'''

    poff = {'all' : {}}

    '''compute pay-off for site 1'''
    poff['o_site'] = site
    poff['o_pay_off'] = pay_off(site, strategies)
    
    
    '''find neighbors (non empty sites)'''        
    nghbs_1 = find_neighbors(site,strategies)

    if len(nghbs_1) == 0:
        poff['best_site'] = site
        poff['best_pay_off'] = poff['o_pay_off']
        return poff
    
    else:
        for n in nghbs_1:
            poff['all'][n] = pay_off(n, strategies)

        poff['all'][site] = poff['o_pay_off']
        best_site = max(poff['all'], key=poff['all'].get)
        poff['best_site'] = best_site
        poff['best_pay_off'] = poff['all'][best_site]

        return poff
    
    
'''Various Update Methods'''


def Fermi_update(poff,strategies,K=0.1):
    '''update strategies by player 1 trying to reproduce the strategy of player 2 with Fermi Temperature'''
     
    '''Fermi Temperature'''
    W =  1/(1+np.exp((poff['o_pay_off']-poff['best_pay_off'])/K))
    rand = np.random.rand()
    
    print "%.2f,%.2f"%(rand,W)

    if rand < W: #and strategies[pay_off['o_site']] <> strategies[pay_off['best_site']]:
        old_str = strategies[poff['o_site']]
        strategies[poff['o_site']]=strategies[poff['best_site']]
        #print "update : %s => %s" %(old_str,strategies[pay_off['o_site']])


def Dirk_update(poff,strategies,r,q):
    '''update strategies by player 1 trying to reproduce the strategy of player 2 with Dirk Temperature'''
    if r==1 and q==0:
        return strategies
    
    elif np.random.rand() > r:
        '''Update with best strategy'''
        old_str = strategies[poff['o_site']]
        strategies[poff['o_site']]=strategies[poff['best_site']]
        #print "update : %s => %s" %(old_str,strategies[pay_off['o_site']])
    
    elif np.random.rand() < q :
        strategies[poff['o_site']] = 1
    else:
        strategies[poff['o_site']] = 0
    
    return strategies            
    
# def swap_strategy(site,strategies,q):
#     
#     s = strategies[site]
#     rand = np.random.rand()
#     
#     if rand < q:
#         strategies[site] = np.abs(s-1) 
#         print "swapped strategies"
#         
#     return strategies



def move(chgDic,strategies):
    '''Move agents'''
    
    origin_best_site_stg = strategies[chgDic['best_site']]
    s0 = strategies.copy() 
    s1 = strategies.copy()
    
    if chgDic['best_site']!=chgDic['o_site']:
    
        #print s1[chgDic['o_site']],s1[chgDic['best_site']]
        
        s1[chgDic['best_site']] = strategies[chgDic['o_site']]
        s1[chgDic['o_site']] = -1
    
        #print s1[chgDic['o_site']],s1[chgDic['best_site']]   
    
        #print "moved agent from %s to %s"%(chgDic['o_site'],chgDic['best_site'])
    
        if origin_best_site_stg > -1:
            s2 = s1.copy()
            ''' if best site was not empty, find a best place for the expelled agent'''
            expellDic = explore_neighborhood(chgDic['best_site'],s2,site_occupation="empty",forceMove=True,plot=False)
            #print expellDic
            
            #print s2[expellDic['o_site']],s2[expellDic['best_site']]
        
            s2[expellDic['best_site']] = origin_best_site_stg

            #print s2[expellDic['o_site']],s2[expellDic['best_site']]
            
            #print "found a new place for expelled agent : from %s to %s"%(expellDic['o_site'],expellDic['best_site'])
            
            strategies = s2.copy()
            return {'strategies' : strategies,'s0' : s0,'s1' : s1,'s2' : s2,'seq' : {0:chgDic['o_site'], 1: chgDic['best_site'],2: expellDic['best_site']}}
        
        else:
            strategies = s1.copy()
            return {'s0' : s0,'s1' : s1,'strategies' : strategies, 'seq' : {0:chgDic['o_site'], 1: chgDic['best_site']}}

    else:
        return {'strategies' : strategies, 'seq' : {0:chgDic['o_site'], 1: chgDic['best_site']}} 
    
    
    
# def testMove(self):
#     initVariables()
# 
#     site = np.random.randint(100)
#     nghbs = search_for_sites(site,strategies_init,site_occupation="occupied")
#     site = nghbs[np.random.randint(len(nghbs))]
# 
#     chgDic = explore_neighborhood(site,strategies_init,site_occupation="occupied",forceMove=True)
#     
#     #print chgDic
#     
#     S = move(chgDic, strategies_init)
#     
#     crop_grid(S['seq'][0],S['s0'],M)
#     print "\n"
#     crop_grid(S['seq'][0],S['s1'],M)
#     print "\n"
#     crop_grid(S['seq'][1],S['s1'],M)
#     print "\n"
#     crop_grid(S['seq'][1],S['s2'],M)


def prisoners_dilemma(player_1,player_2,strategies):       
    ''' strategy set for prisoners dilemma'''
    #T,R,P,S = (1.02,1.0,0.0,0.0) # standard set
    T,R,P,S = (1.3,1.0,0.1,0.0) # Helbing Yu set
    
    #T,R,P,S = (1.0,1.0,0.0,0.0) # cooperators = 0.6
    #T,R,P,S = (1.05,1.0,0.0,0.0) # cooperators = 0.1 (found approx. 0.45)
    #T,R,P,S = (1.1,1.0,0.0,0.0) # cooperators = 0.0 (found approx. 0.27)
    #T,R,P,S = (1.2,1.0,0.0,0.0) # cooperators = 0.0 (found approx. 0.25)
    #T,R,P,S = (1.3,1.0,0.0,0.0) # cooperators = 0.0 (found approx. 0.19)
    #T,R,P,S = (1.7,1.0,0.0,0.0) # cooperators = 0.0 (found approx. 0.13)
    
    GAME_SET = {(1,1):(R,R),(1,0):(S,T),(0,1):(T,S),(0,0):(P,P)}
    
    if isinstance(player_1,int) or isinstance(player_1,float):
        (p1,p2) = GAME_SET[(strategies[player_1],strategies[player_2])]
    elif len(player_1) == 2:
        (p1,p2) = GAME_SET[(player_1[1],strategies[player_2])]

    return (p1,p2)



''' Mobility''' 
def search_for_sites(site,strategies,site_occupation="all"):
    '''search for site within the (2M + 1) x (2M + 1) Moore's neighborhood '''
    ''' options for occupation : 'all','occupied','empty' '''
    
    M = initDic['M']
    
    l = len(strategies.keys())
    size=np.sqrt(l)
                
    Y = np.arange(site-M*size,site+(M+1)*size,size)    
    X = np.arange(-M,M+1)

    nghbs = []
        
    for i,ix in enumerate(X):
        nghbs = np.append(nghbs,Y+ix)
      
    nghbs = nghbs%l
    
    nghbs = list(nghbs)
    nghbs.remove(site)
    
    delete = []
    
    if site_occupation == 'occupied':
        for i,ix in enumerate(nghbs):
            if strategies[ix] < 0:
                delete.append(i)
                
        
    if site_occupation == 'empty':
        for i,ix in enumerate(nghbs):
            if strategies[ix] > -1:
                delete.append(i)
        
    nghbs = np.delete(nghbs,delete)

    return nghbs


 
def explore_neighborhood(site,strategies,site_occupation="all",forceMove=False,plot=False):
    '''Find neighboring sites with with better pay-off'''
    
    neighbor_sites = search_for_sites(site,strategies,site_occupation=site_occupation)
        
    poff = {}

    if not strategies[site]==-1:
        ownPayOff = pay_off(site,strategies)
        poff[site] = ownPayOff
    else:
        print "no strategy at this site"
        return 0

    if forceMove:
        poff.pop(site)

    for i,ix in enumerate(neighbor_sites):             
        if strategies[ix] == -1:
            poff[ix] = pay_off([ix,strategies[site]],strategies)
        else: 
            poff[ix] = pay_off(ix,strategies)
        
        '''Add some random noise in case two sites have equal pay-off'''
        poff[ix] = poff[ix] + (np.random.rand()-0.5)/10000.
    
    best_site = max(poff, key=poff.get)
    
    return {'o_site': int(site), 'o_pay_off' :np.round(ownPayOff,4), 'best_site':int(best_site), 'best_pay_off' : np.round(poff[best_site],4) }





def oneStep(strategies):
    
    '''pick an agent randomly'''
    site = choice(strategies.keys())

    if strategies[site]==-1:
        '''if randomly chosen site is empty, continue'''
        return strategies

    '''Migration'''
    if np.random.rand() < m:
        if np.random.rand() < s:
            '''Migration to best possible site (property game)'''
            chgDic = explore_neighborhood(site,strategies,site_occupation="all")

        else:
            '''Migration to an empty site'''
            chgDic = explore_neighborhood(site,strategies,site_occupation="empty")
                     
        strategies = move(chgDic,strategies)['strategies']
        site = chgDic['best_site']
        comparison = play_with_all_neighbors(site,strategies)                

    else:
        '''no movement, compare pay-off with neighbors'''
        comparison = play_with_all_neighbors(site,strategies)
        if not comparison.has_key('best_site'):
            return strategies

    '''Update strategy given comparison with neighbors'''            
    strategies = Dirk_update(comparison,strategies,r,q)

    return strategies


def simulate(verbose=0):
    
    init_timestamp = datetime.now() 
    init_T = time.mktime(init_timestamp.timetuple())
    
    strategies_init = initialize_grid(initDic['grid_size'],initDic['perc_filled_sites'])    
    strategies = strategies_init.copy()
    
    coop = np.array(strategies.values())
    empty = len(coop[coop==-1])
    
    cLevel = coopLevel(strategies)
    
    C={'iteration':[0],'c':[cLevel['c']],'d':[cLevel['d']],'e' : [cLevel['e']]}

    MCS = initDic['iterations']*initDic['grid_size']**2
    
    dic = {'init_timestamp' : init_T, 'input': initDic}
    dic['input']['strategy_init'] = strategies_init
    
        
    for i in range(MCS):
        if i==range(MCS)[-iterations]:
            strategies_step_before = strategies.copy()
        
        strategies = oneStep(strategies)
    
        cLevel = coopLevel(strategies)
        
        '''conditions for breaking the loop'''
        if len(np.argwhere(np.array(C['c'][-5:])==C['c'][-1]))==5:
            print "frozen situation, stop !\n"
            break
        
        if cLevel['c']==0:
            print "no cooperator left"
            break
        
        if cLevel['d']==0:
            print "no defector left"
            break
        
        if i%(iterations-1)==0 and np.max(C['c'][-3:]) < 0.01:
            print "lower threshold of cooperators reached"
            break
        
        if i%iterations==0:
            C['iteration'].append(i)
            C['c'].append(cLevel['c'])
            C['d'].append(cLevel['d'])
            C['e'].append(cLevel['e'])
            if verbose >1:
                print "%s (%.2f perc.),cooperation level : %.2f percent"%(i,float(i)/MCS*100,C['c'][-1]*100)
            

        
    if verbose > 0:
        print "initial configuration: M=%s, r=%s, q=%s, m=%s, s=%s"%(M,r,q,m,s)
        print "empty_sites : %s" %cLevel['e']
        print "defectors : %s" %cLevel['c']
        print "cooperators : %s"%cLevel['d']
    
        crop_grid(0,strategies_init,10)
        print "\n"
        crop_grid(0,strategies,10)
    
    
    '''Prepare Output'''
    now = datetime.now()
    last_T = time.mktime(now.timetuple())
    
    dic['last_timestamp'] = last_T
    dic['duration'] = last_T - init_T
    dic['output'] = {'filled_sites' : len(coop[coop!=-1]),
                     'iterations' : i,
                     'defectors' : cLevel['d'],
                     'cooperators' : cLevel['c'],   
                     'strategies_final' : strategies,
                     'strategies_step_before': strategies_step_before,
                     'cooperation' : C
                        }

    return dic

    
    '''
    if save:
        J = json.dumps(dic)
        f = open("results/json/simul%s_grid%s_%s_r%s_q%s_m%s_s%s_M%s.json"%(iterations,grid_size,datetime.strftime(init_timestamp,'%Y%m%d%H%M%S'),r,q,m,s,M),'wb')
        f.write(J)
        f.close()
     
    J = json.dumps(dic)
    key = bucket.new_key("results/json/simul%s_grid%s_%s_r%s_q%s_m%s_s%s_M%s.json"%(iterations,grid_size,datetime.strftime(init_timestamp,'%Y%m%d%H%M%S'),r,q,m,s,M))
    key.set_contents_from_string(J)
    
    '''


def testExpell(self):
    initVariables()
    global s
    for s in [0.5]:
        k=0
        while k<3:
            print "configuration: M=%s, r=%s, q=%s, m=%s, s=%s"%(M,r,q,m,s)
            strategies_init = initialize_grid(STRATEGY_SET,size = grid_size, perc_filled_sites = perc_filled_sites)
            strategies,C,strategies_init =  simulate2()
            k+=1
    





if __name__ == '__main__':
      
    grid_size = 49
    iterations = 200
    perc_filled_sites = 0.5
    
    '''probability not to copy best strategy'''
    r = 0.05
    '''probability to cooperate spontaneously (noise 1)'''
    q = 0.05
    '''Probability to Migrate'''
    m = 1
    '''probability of expelling'''
    s = 1
    '''Moore's Distance'''
    M = 5
    
    
    initDic = { 'grid_size' : grid_size,'iterations' : iterations, 'perc_filled_sites' : perc_filled_sites,
            'r':r,'q':q,'m':m,'s':s,'M':M}
    
    

    
    '''
    strategies,cooperation,strategies_init = PG.simulate()
    
    grid_init = np.array(strategies_init.values()).reshape([grid_size,grid_size]) 
    print grid_init[0:20,0:20]
    
    print "\n"
    grid = np.array(strategies.values()).reshape([grid_size,grid_size])    
    print grid[0:20,0:20]
    '''
    
