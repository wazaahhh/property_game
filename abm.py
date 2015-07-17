#from matplotlib import use, get_backend
#if 'Agg' != get_backend().title(): 
#    use('Agg')
import sys
import numpy as np
#import pylab as pl
from random import choice,randrange, shuffle
import time
from datetime import datetime
import json
import boto

global bucketName
bucketName = "property_game"

def S3connectBucket(bucketName):
    s3 = boto.connect_s3()
    bucket = s3.get_bucket(bucketName)
    return bucket

def changeTypeKeysDic(dic,type=int):
    for k in dic.keys():
        dic[int(k)] = dic.pop(k)
    return dic

global bucket 
bucket = S3connectBucket("property_game")

class property_game():
    
    def __init__(self):
        self.iconn = None
        self.sconn = None
    
    def coopLevel(self,strategies):
        coop = np.array(strategies.values())
        cooperators = float(len(coop[coop==1]))/len(coop[coop>=0])
        defectors = float(len(coop[coop==0]))/len(coop[coop>=0])
        empty = float(len(coop[coop < 0]))/len(coop)
        return {'c' : cooperators,'d' : defectors,'e':empty}
    
    
    def initialize_grid(self,size,perc_filled_sites):
        '''initialize grid with an equi-probable set of each strategy specified in STRATEGY_SET, among all non-exmpty sites (defined by perc_filled_sites)'''
    
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
    
    
    def strKeysToInt(self,strategies):
        
        new_strategies = {}
        
        for key in strategies.keys():
            new_strategies[int(key)] = strategies[key]
    
        return new_strategies
    
    def makeInitConditions(self,initDic):
        strategies = self.initialize_grid(initDic['grid_size'], initDic['perc_filled_sites'])
        key = bucket.new_key("initial_conditions/initGrid/initGrid_simul%s_grid%s_filled%s.json"%(initDic['iterations'],initDic['grid_size'],initDic['perc_filled_sites']))
        key.set_contents_from_string(json.dumps(strategies))
        
        randInt = list(np.random.randint(0,max(strategies.keys())+1,iterations*grid_size**2))
        key = bucket.new_key("initial_conditions/initRandInt/initRandInt_simul%s_grid%s_filled%s.json"%(initDic['iterations'],initDic['grid_size'],initDic['perc_filled_sites']))
        key.set_contents_from_string(json.dumps(randInt))
        
        return {'strategies' : strategies, 'randInt' : randInt}
    
    
    def loadInitConditions(self,initDic):
        key = "initial_conditions/initGrid/initGrid_simul%s_grid%s_filled%s.json"%(initDic['iterations'],initDic['grid_size'],initDic['perc_filled_sites'])
        print key
        k = bucket.get_key(key)
        strategies_init = json.loads(k.get_contents_as_string())
        #key = bucket.get_key("initial_conditions/initRandInt/initRandInt_simul%s_grid%s_filled%s.json"%(initDic['iterations'],initDic['grid_size'],initDic['perc_filled_sites']))
        #randInt = np.array(json.loads(key.get_contents_as_string()))
        
        return {'strategies' : strategies_init}
        
        
    def make_grid(self,strategies):
        '''Turns a strategy dictionary into a command line viewable grid'''
        
        
        values  = []
        for key in sorted(strategies):
            values.append(strategies[key])
        
        grid = np.array(values).reshape([grid_size,grid_size])    
        return grid


    def crop_grid(self,site,strategies,M):
        ''' specifies a region of interest, for large grids'''
        
        grid = self.make_grid(strategies)
        grid_size = len(grid)
        
        if site < 0 or site > grid_size**2-1:
            print "error site out of bounds"
        
        index_x = np.arange(site/grid_size-M,site/grid_size+M+1)%grid_size
        index_y = np.arange(site%grid_size-M,site%grid_size+M+1)%grid_size
        
        index = np.meshgrid(index_x,index_y)
        
        print grid[index].T
        
        if len(grid)==0:
            print blah


    '''Basic Evolutionary Game Theory Tools'''
            
    def find_neighbors(self,site,strategies,non_empty_sites=True):
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


    def pay_off(self,site,strategies):
        '''find overall pay-off for site, i.e.,play simultaneously with all neighbors'''
        
        
        '''find neighbors (non empty sites)'''  
        if isinstance(site,int) or isinstance(site,float):
            nghbs_1 = self.find_neighbors(site,strategies)
        elif len(site) == 2:
            nghbs_1 = self.find_neighbors(site[0],strategies)
            
        pay_off = []

        for i,ix in enumerate(nghbs_1):
            p1 = self.prisoners_dilemma(site,ix,strategies)[0]
            pay_off = np.append(pay_off,p1)
            
        return np.sum(pay_off)


    def play_with_random_neighbor(self,site,strategies):
        '''play with a random neighbor'''
        
        pay_off = {'o_site' : site, 'o_pay_off' : self.pay_off(site, strategies)}
        
        
        '''find neighbors (non empty sites)'''        
        nghbs_1 = self.find_neighbors(site,strategies)
        
        '''randomly select a neighbor (non empty site)'''
        if len(nghbs_1)>0:
            site_2 = choice(nghbs_1)

        else:
            #print "no neighbor"
            return pay_off
        
        pay_off['site_2'] = site_2
        pay_off['site2_pay_off'] = self.pay_off(site_2, strategies) 
                         
        return pay_off



    def play_with_all_neighbors(self,site,strategies):
        '''play with all four nearest neighbors'''

        pay_off = {'all' : {}}

        '''compute pay-off for site 1'''
        pay_off['o_site'] = site
        pay_off['o_pay_off'] = self.pay_off(site, strategies)
        
        
        '''find neighbors (non empty sites)'''        
        nghbs_1 = self.find_neighbors(site,strategies)

        if len(nghbs_1) == 0:
            pay_off['best_site'] = site
            pay_off['best_pay_off'] = pay_off['o_pay_off']
            return pay_off
        
        else:
            for n in nghbs_1:
                pay_off['all'][n] = self.pay_off(n, strategies)

            pay_off['all'][site] = pay_off['o_pay_off']
            best_site = max(pay_off['all'], key=pay_off['all'].get)
            pay_off['best_site'] = best_site
            pay_off['best_pay_off'] = pay_off['all'][best_site]

            return pay_off

  
    def Fermi_update(self,pay_off,strategies,K=0.1):
        '''update strategies by player 1 trying to reproduce the strategy of player 2 with Fermi Temperature'''
         
        '''Fermi Temperature'''
        W =  1/(1+np.exp((pay_off['o_pay_off']-pay_off['best_pay_off'])/K))
        rand = np.random.rand()
        
        print "%.2f,%.2f"%(rand,W)

        if rand < W: #and strategies[pay_off['o_site']] <> strategies[pay_off['best_site']]:
            old_str = strategies[pay_off['o_site']]
            strategies[pay_off['o_site']]=strategies[pay_off['best_site']]
            #print "update : %s => %s" %(old_str,strategies[pay_off['o_site']])


    def Dirk_update(self,pay_off,strategies,r,q):
        '''update strategies by player 1 trying to reproduce the strategy of player 2 with Dirk Temperature'''
        if r==1 and q==0:
            return strategies
        
        elif np.random.rand() > r:
            '''Update with best strategy'''
            old_str = strategies[pay_off['o_site']]
            strategies[pay_off['o_site']]=strategies[pay_off['best_site']]
            #print "update : %s => %s" %(old_str,strategies[pay_off['o_site']])
        
        elif np.random.rand() < q :
            strategies[pay_off['o_site']] = 1
        else:
            strategies[pay_off['o_site']] = 0
        
        return strategies            
        
    def swap_strategy(self,site,strategies,q):
        
        s = strategies[site]
        rand = np.random.rand()
        
        if rand < q:
            strategies[site] = np.abs(s-1) 
            print "swapped strategies"
            
        return strategies
    
    
    def prisoners_dilemma(self,player_1,player_2,strategies):       
        ''' strategy set for prisoners dilemma'''
        #T,R,P,S = (1.02,1.0,0.0,0.0) # standard set
        T,R,P,S = (1.3,1.0,0.1,0.0) # Helbing Yu set

        GAME_SET = {(1,1):(R,R),(1,0):(S,T),(0,1):(T,S),(0,0):(P,P)}
        
        if isinstance(player_1,int) or isinstance(player_1,float):
            (p1,p2) = GAME_SET[(strategies[player_1],strategies[player_2])]
        elif len(player_1) == 2:
            (p1,p2) = GAME_SET[(player_1[1],strategies[player_2])]

        return (p1,p2)
 
 
    ''' Mobility''' 
    def search_for_sites(self,site,strategies,site_occupation="all"):
        '''search for site within the (2M + 1) x (2M + 1) Moore's neighborhood '''
        ''' options for occupation : 'all','occupied','empty' '''
        
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
 
     
    def explore_neighborhood(self,site,strategies,site_occupation="all",forceMove=False,plot=False):
        '''Find neighboring sites with with better pay-off'''
        
        neighbor_sites = self.search_for_sites(site,strategies,site_occupation=site_occupation)
            
        pay_off = {}
    
    
        if not strategies[site]==-1:
            ownPayOff = self.pay_off(site,strategies)
            pay_off[site] = ownPayOff
        else:
            print "no strategy at this site"
            return 0
    
        if forceMove:
            pay_off.pop(site)
    
        for i,ix in enumerate(neighbor_sites):             
            if strategies[ix] == -1:
                pay_off[ix] = self.pay_off([ix,strategies[site]],strategies)
            else: 
                pay_off[ix] = self.pay_off(ix,strategies)
            
            '''Add some random noise in case two sites have equal pay-off'''
            pay_off[ix] = pay_off[ix] + (np.random.rand()-0.5)/10000.
        
        best_site = max(pay_off, key=pay_off.get)
        
        return {'o_site': int(site), 'o_pay_off' :np.round(ownPayOff,4), 'best_site':int(best_site), 'best_pay_off' : np.round(pay_off[best_site],4) }
   
    def move(self,chgDic,strategies):
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
                expellDic = self.explore_neighborhood(chgDic['best_site'],s2,site_occupation="empty",forceMove=True,plot=False)
                #print expellDic
                
                #print s2[expellDic['o_site']],s2[expellDic['best_site']]
            
                s2[expellDic['best_site']] = origin_best_site_stg
    
                #print s2[expellDic['o_site']],s2[expellDic['best_site']]
                
                #print "found a new place for expelled agent : from %s to %s"%(expellDic['o_site'],expellDic['best_site'])
                
                strategies = s2.copy()
                return {'strategies' : strategies,'s0' : s0,'s1' : s1,'s2' : s2,'seq' : {0:chgDic['o_site'], 1: chgDic['best_site'],2: expellDic['best_site']},'mv': {chgDic['o_site'] : -1,chgDic['best_site'] : s1[chgDic['best_site']], expellDic['best_site'] : s2[expellDic['best_site']] }}
            
            else:
                strategies = s1.copy()
                return {'s0' : s0,'s1' : s1,'strategies' : strategies, 'seq' : {0:chgDic['o_site'], 1: chgDic['best_site']},'mv': {chgDic['o_site'] : -1,chgDic['best_site'] : s1[chgDic['best_site']]}}

        else:
            return {'strategies' : strategies, 'seq' : {0:chgDic['o_site'], 1: chgDic['best_site']},'mv'  : {chgDic['o_site'] : strategies[chgDic['o_site']]}}
 
    def testMove(self):
        self.initVariables()

        site = np.random.randint(100)
        nghbs = self.search_for_sites(site,strategies_init,site_occupation="occupied")
        site = nghbs[np.random.randint(len(nghbs))]

        chgDic = self.explore_neighborhood(site,strategies_init,site_occupation="occupied",forceMove=True)
        
        #print chgDic
        
        S = self.move(chgDic, strategies_init)
        
        self.crop_grid(S['seq'][0],S['s0'],M)
        print "\n"
        self.crop_grid(S['seq'][0],S['s1'],M)
        print "\n"
        self.crop_grid(S['seq'][1],S['s1'],M)
        print "\n"
        self.crop_grid(S['seq'][1],S['s2'],M)
        
     
    def oneStep(self,strategies,site):
        '''pick an agent randomly'''
        #site = choice(strategies.keys())
        
        if strategies[site]==-1:
            '''if randomly chosen site is empty, continue'''
            moves = {}
            return strategies,moves

        #print 'init : ',site,strategies[site]
    
        '''Migration'''
        if np.random.rand() < m:
            if np.random.rand() < s:
                '''Migration to best possible site (property game)'''
                chgDic = self.explore_neighborhood(site,strategies,site_occupation="all")
    
            else:
                '''Migration to an empty site'''
                chgDic = self.explore_neighborhood(site,strategies,site_occupation="empty")
            
            mv = self.move(chgDic,strategies)
            strategies = mv['strategies']
            
            moves = mv['mv']
            #print 'moves:', moves
            
            site = chgDic['best_site']
            comparison = self.play_with_all_neighbors(site,strategies)                
    
        else:
            '''no movement, compare pay-off with neighbors'''
            comparison = self.play_with_all_neighbors(site,strategies)
            if not comparison.has_key('best_site'):
                return strategies,moves
    
        '''Update strategy given comparison with neighbors'''            
        strategies = self.Dirk_update(comparison,strategies,r,q)
        try:
            moves[site] = strategies[site]
        except:
            moves = {site : strategies[site]}
        #print 'update :', moves
    
        return strategies,moves
        
        
    

    
    def simulate(self,initDic,uploadToS3=True,verbose=0,resumeKey=None,loadStrategies=None,maxHours = 11):
        
        self.initVariables(initDic)
        
        init_timestamp = datetime.now() 
        init_T = time.mktime(init_timestamp.timetuple())
        
        MCS = iterations*grid_size**2
        
        if resumeKey:
            
            print "resuming simulation: ", resumeKey
            
            maxHours = 24*5 # make sure the simulation goes to the end            
            
            
            k = bucket.get_key(resumeKey)
            retrieveDic = json.loads(k.get_contents_as_string())        
            initDic = retrieveDic['input']
            
            self.initVariables(initDic)
            init_T = retrieveDic['init_timestamp']
            #last_iter = len(retrieveDic['output']['strategies_iter'].keys())
            i = retrieveDic['output']['iterations']
            #grid_size = retrieveDic['input']['grid_size']
            
            MCS = iterations*grid_size**2
            print grid_size,iterations,i, MCS
            
            strategies_init = changeTypeKeysDic(retrieveDic['output']['strategies_final'],type=int)
            strategies_iter = changeTypeKeysDic(retrieveDic['output']['strategies_iter'],type=int)
            
            strategies = strategies_init.copy()
            
            coop = np.array(strategies_init.values())
            empty = len(coop[coop==-1])
            cLevel = self.coopLevel(strategies_init)
            
            #print strategies_init.keys()
            #print np.min(strategies_init.keys()),np.max(strategies_init.keys())
            
            randInt = np.random.randint(np.min(strategies_init.keys()),np.max(strategies_init.keys()),MCS)
            
            C = retrieveDic['output']['cooperation']
            UpdateList = retrieveDic['output']['mv']
            
            dic = retrieveDic
            
            
        elif loadStrategies:
            try:
                #initConditions = self.loadInitConditions(initDic)
                #strategies_init = self.strKeysToInt(initConditions['strategies'])
                strategies_init = changeTypeKeysDic(json.loads(bucket.get_key(loadStrategies).get_contents_as_string()),type=int)
                randInt = np.random.randint(np.min(strategies_init.keys()),np.max(strategies_init.keys()),MCS)
                #randInt = initConditions['randInt']
                print "initial conditions successfully loaded"
            except:
                print 'create initial conditions'
                initConditions = self.makeInitConditions(initDic)
                strategies_init = initConditions['strategies']
                randInt = initConditions['randInt']
        else:
            strategies_init = self.initialize_grid(grid_size,perc_filled_sites)
            randInt = np.random.randint(np.min(strategies_init.keys()),np.max(strategies_init.keys()),MCS)
        
        if not resumeKey:
            '''Nasty condition to integrate the resume simulation with old code'''
            strategies = strategies_init.copy()
        
            coop = np.array(strategies.values())
            empty = len(coop[coop==-1])
            cLevel = self.coopLevel(strategies)
        
            C = {'iteration':[0],'c':[cLevel['c']],'d':[cLevel['d']],'e' : [cLevel['e']]}
        
            dic = {'init_timestamp' : init_T, 'input': initDic}
            dic['input']['strategy_init'] = strategies_init
        
            i=0
        
        strategies_iter = {}
        
        
        
        for site in randInt[i:]:
            i+=1
            strategies,moves = self.oneStep(strategies,site)
            
            
            try:
                UpdateList.append(np.array(moves.items()).tolist())
            except:
                UpdateList = [np.array(moves.items()).tolist()]
        
            cLevel = self.coopLevel(strategies)
            
            '''conditions for breaking the loop'''
            if len(np.argwhere(np.array(C['c'][-10:])==C['c'][-1]))==10:
                print "frozen situation, stop !\n"
                break
            
            if cLevel['c']==0:
                print "no cooperator left"
                break
            
            if cLevel['d']==0:
                print "no defector left"
                break
            
            if i%(grid_size**2-1)==0 and np.max(C['c'][-3:]) < 0.01:
                print "lower threshold of cooperators reached"
                break
            
            if i%(grid_size**2+1)==0:
                strategies_step_before = strategies.copy()
                strategies_iter[i] = strategies
                
                #print i, "strategies recorded"
            
            if i%(grid_size**2)==0:
                C['iteration'].append(i)
                C['c'].append(cLevel['c'])
                C['d'].append(cLevel['d'])
                C['e'].append(cLevel['e'])
                if verbose >1:
                    print "%s (%.2f perc.),cooperation level : %.2f percent"%(i,float(i)/MCS*100,C['c'][-1]*100)
                
                now_T = time.mktime(datetime.now().timetuple())
                
                if (now_T - init_T)/3600. > maxHours:
                    print "maximum simulation time reached %s. Finishing."%maxHours
                    break
            
        if verbose > 0:
            print "final step",i
            print "initial configuration: M=%s, r=%s, q=%s, m=%s, s=%s"%(M,r,q,m,s)
            print "empty_sites : %s" %cLevel['e']
            print "defectors : %s" %cLevel['d']
            print "cooperators : %s"%cLevel['c']
        
            self.crop_grid(0,strategies_init,10)
            print "\n"
            self.crop_grid(0,strategies,10)
        
        
        '''Prepare Output'''
        now = datetime.now()
        last_T = time.mktime(now.timetuple())
        
        dic['last_timestamp'] = last_T
        dic['duration'] = last_T - init_T
        dic['output'] = {'filled_sites' : len(coop[coop!=-1]),
                         'iterations' : i,
                         'defectors' : cLevel['d'],
                         'cooperators' : cLevel['c'],
                         'strategies_iter' : strategies_iter,
                         'strategies_final' : strategies,
                         'strategies_step_before': strategies_step_before,
                         'cooperation' : C,
                         'mv' : UpdateList
                            }
        
        if uploadToS3:
            J = json.dumps(dic)
            key = bucket.new_key("results/json/simul%s_grid%s_filled%.2f_%s_r%.2f_q%.2f_m%.2f_s%.4f_M%s.json"%(iterations,grid_size,perc_filled_sites,datetime.strftime(datetime.fromtimestamp(dic['init_timestamp']),'%Y%m%d%H%M%S'),r,q,m,s,M))
            key.set_contents_from_string(J)
            print "results uploaded to S3"
            #return dic
        else:
            return dic    

#    def continueSimulate(self,key):
#        '''Resume a simulation'''
#        k = bucket.get_key(key)
#        retrieveDic = json.loads(k.get_contents_as_string())        
#        initDic = retrieveDic['input']
#        last_iter = len(retrieveDic['output']['strategies_iter'].keys())
#        initConditions = retrieveDic['output']['strategies_final']
        
        
        return dic
      
    def initVariables(self,initDic):
        
        global grid_size
        grid_size = initDic['grid_size']
        global iterations
        iterations = initDic['iterations']
        global perc_filled_sites
        perc_filled_sites = initDic['perc_filled_sites']
        global r
        r = initDic['r']
        global q
        q = initDic['q']
        global m
        m = initDic['m']
        global s
        s = initDic['s']
        global M
        M = initDic['M']

        global strategies_init     
        global grid


    def makeJsonList(self):
        list = bucket.list("results/json/")
        
        output = []
        for key in list:
            print key.name
            url = "https://s3.amazonaws.com/%s/%s"%(bucketName,key.name)
            output.append(url)
        
        key = bucket.new_key("results/list.json")
        key.set_contents_from_string(output)
        
        print output
        
if __name__ == '__main__':
    

    '''
    initDic = { 'grid_size' : grid_size,'iterations' : iterations, 'perc_filled_sites' : perc_filled_sites,
            'r':r,'q':q,'m':m,'s':s,'M':M}'''

    initDic = { 'grid_size' : 49,'iterations' : 200, 'perc_filled_sites' : 0.5,
            'r':0.0,'q':0.0,'m':1,'s':0.1555,'M':5}
    
    
    PG = property_game()
    #dic = PG.simulate(initDic,uploadToS3=True,verbose=2)
    

'''
Todo:
- fix initial conditions and random steps to ease comparison between scenarios
- design a way to test whether property violation can help the outbreak of cooperation ?
'''

    
