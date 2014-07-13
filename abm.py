from matplotlib import use, get_backend
if 'Agg' != get_backend().title(): 
    use('Agg')

import numpy as np
import pylab as pl
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

global bucket 
bucket = S3connectBucket("property_game")

class property_game():


    def __init__(self):
        self.iconn = None
        self.sconn = None
    
 
    
    def initialize_grid(self,STRATEGY_SET,size=100,perc_filled_sites=1):
        '''initialize grid with an equi-probable set of each strategy specified in STRATEGY_SET, 
        mong all non-exmpty sites (defined by perc_filled_sites)'''

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
         
        '''assign strategies'''
        strategies = {}
         
        i=0
        
        #print np.sort(subgrid)
        
        shuffle(subgrid)
        
        for i,ix in enumerate(subgrid):
            strategies[ix]=choice(STRATEGY_SET.values())
        
        for i,ix in enumerate(rest):
            strategies[ix]=-1
            
        return strategies
         
    
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
    
        #index_x = np.arange(site%grid_size-M,site%grid_size+M+1)
        #index_y = np.arange(site/grid_size-M,site/grid_size+M+1)
        
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
        '''find overall pay-off for site, i.e.,
        play simultaneously with all neighbors'''
        
        
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



    def  play_with_all_neighbors(self,site,strategies):
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
                return {'strategies' : strategies,'s0' : s0,'s1' : s1,'s2' : s2,'seq' : {0:chgDic['o_site'], 1: chgDic['best_site'],2: expellDic['best_site']}}
            
            else:
                strategies = s1.copy()
                return {'s0' : s0,'s1' : s1,'strategies' : strategies, 'seq' : {0:chgDic['o_site'], 1: chgDic['best_site']}}

        else:
            return {'strategies' : strategies, 'seq' : {0:chgDic['o_site'], 1: chgDic['best_site']}} 
 
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
        
        
    def simulate2(self,plot=True,save=True):
        
        init_timestamp = datetime.now() 
        init_T = time.mktime(init_timestamp.timetuple())
       
        #self.initVariables()
        
        strategies = strategies_init.copy()
        
        strategi = {}
        coop = np.array(strategies.values())
        empty = len(coop[coop==-1])
        
        C={'x':[],'y':[]}

        
        dic = {'init_timestamp' : init_T, 
               'input': {
                'grid_size' : grid_size,
                'iterations' : iterations,
                'filled_sites' : perc_filled_sites,
                'strategies_init' : strategies_init,
                'r':r,'q':q,'m':m,'s':s,'M':M,
                        }
               }
        
        cooperation = []
        
        coop = np.array(strategies.values())
        cooperation.append(float(np.sum(coop[coop>0]))/len(coop[coop>=0]))
        print cooperation[0]
        
        
        for i in range(MCS):
            
            if i==range(MCS)[-iterations]:
                strategies_step_before = strategies.copy()
            
            '''pick an agent randomly'''
            site = choice(strategies.keys())
            
            if strategies[site]==-1:
                '''if randomly chosen site is empty, continue'''
                #print "empty site %s (%s)"%(site,strategies[site])
                
                try:
                    cooperation.append(cooperation[-1])
                    continue
                except:
                    cooperation.append(0)
                    continue

            '''Migration'''
            if np.random.rand() < m:
                if np.random.rand() < s:
                    '''Migration to best possible site (property game)'''
                    chgDic = self.explore_neighborhood(site,strategies,site_occupation="all",forceMove=False,plot=False)
 
                else:
                    '''Migration to an empty site'''
                    chgDic = self.explore_neighborhood(site,strategies,site_occupation="empty",forceMove=False,plot=False)
                                 
                strategies = self.move(chgDic,strategies)['strategies']
                site = chgDic['best_site']
                comparison = self.play_with_all_neighbors(site,strategies)                
            
            else:
                '''no movement, compare pay-off with neighbors'''
                comparison = self.play_with_all_neighbors(site,strategies)
                if not comparison.has_key('best_site'):
                    continue

            '''Update strategy given comparison with neighbors'''            
            strategies = self.Dirk_update(comparison,strategies,r,q)
        
            '''                
            nghbs = self.search_for_sites(site,strategies,site_occupation="empty")
            o_site = site.copy()
            site = nghbs[np.random.randint(len(nghbs))]
            #print "new site : %s (strategy : %s)"%(site,strategies[site])
            #pay_off = self.pay_off(site,strategies)
            chgDic = {'best_pay_off': 0, 'best_site': site, 'o_pay_off': 1.5, 'o_site': o_site }
            strategies = self.move(chgDic,strategies)['strategies']
            #print "new site : %s (strategy : %s)"%(site,strategies[site])
            comparison = self.play_with_all_neighbors(site,strategies)
            '''
            
               
            coop = np.array(strategies.values())
            cooperation.append(float(np.sum(coop[coop>0]))/len(coop[coop>=0]))
            
            n = 50000
            if len(np.argwhere(np.array(cooperation[-n:])==cooperation[-1]))==n:
                print "frozen situation, stop !\n"
                break
            
            if len(coop[coop==1])==0:
                print "no cooperator left"
                break
            
            if len(coop[coop==0])==0:
                print "no defector left"
                break
            
            if i%(iterations-1)==0 and np.max(cooperation) < 0.01:
                print "lower threshold reached"
                break
            
            if i%iterations==0:
                C['x'].append(i)
                C['y'].append(cooperation[-1])
                print "%s (%.2f perc.),%s,cooperation level : %.2f percent"%(i,float(i)/MCS*100,site,cooperation[-1]*100)
                #strategi[i]= strategies
                cooperation=[]

            
        
        print "initial configuration: M=%s, r=%s, q=%s, m=%s, s=%s"%(M,r,q,m,s)
        
        print "empty_sites : %s" %len(coop[coop==-1])
        print "defectors : %s" %len(coop[coop==0])
        print "cooperators : %s"%len(coop[coop==1])
        
        
        
        
        
        self.crop_grid(0,strategies_init,10)
        print "\n"
        self.crop_grid(0,strategies,10)
        
        now = datetime.now()
        last_T = time.mktime(now.timetuple())
        
        
        dic['last_timestamp'] = last_T
        dic['duration'] = last_T - init_T
        dic['output'] = {'filled_sites' : len(coop[coop!=-1]),
                         'iterations' : i,
                         'defectors' : len(coop[coop==0]),
                         'cooperators' : len(coop[coop==1]),   
                         'strategies_final' : strategies,
                         'strategies_step_before': strategies_step_before,
                         'cooperation' : C
                            }
        '''
        if plot:
            pl.figure(1)
            pl.plot(C['x'],C['y'],'-')
            pl.xlabel("Monte Carlo Steps (MCS)")
            pl.ylabel("proportion of cooperators")
            pl.ylim(0,1)
            pl.savefig("results/figures/simul%s_grid%s_%s_r%s_q%s_m%s_s%s_M%s.png"%(iterations,grid_size,datetime.strftime(init_timestamp,'%Y%m%d%H%M%S'),r,q,m,s,M))
            pl.close()
        
        if save:
            J = json.dumps(dic)
            f = open("results/json/simul%s_grid%s_%s_r%s_q%s_m%s_s%s_M%s.json"%(iterations,grid_size,datetime.strftime(init_timestamp,'%Y%m%d%H%M%S'),r,q,m,s,M),'wb')
            f.write(J)
            f.close()
         '''
        J = json.dumps(dic)
        key = bucket.new_key("results/json/simul%s_grid%s_%s_r%s_q%s_m%s_s%s_M%s.json"%(iterations,grid_size,datetime.strftime(init_timestamp,'%Y%m%d%H%M%S'),r,q,m,s,M))
        key.set_contents_from_string(J)
        
            
        return dic
 
 
#     
#     def migration_empty(self,M,noise_2=0):
#         '''Migrate to an empty cell within (2M + 1 ) x ( 2M + 1 ) neighborhood. If several sites have the same best pay-off, take the closest one.
#         If noise_2<>0 relocation with some probability
#         ''' 
#     
#     def migration_replace(self,M,s,empty_first=True):    
#         ''' migrate to a filled cell within (2M + 1) x (2M + 1) neighborhood and the individual who occupied this place goes to the best empty cell in her migration range.
#         If empty_first is True, the agent will first try to find a second best empty cell in the    migration area.
#         '''


    def prisoners_dilemma(self,player_1,player_2,strategies):       
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


    def initVariables(self):
        
        
        global STRATEGY_SET
        global grid_size
        global iterations
        global MCS
        global perc_filled_sites
        global r
        global q
        global m
        global s 
        global M 
        global strategies_init     
        global grid
        
        
        STRATEGY_SET = {'C':1,'D':0}
        grid_size = 49
        iterations = 200
        MCS = (grid_size**2)*iterations # Monte Carlo Steps
        
        '''Grid Sparsity'''
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
        
        strategies_init = self.initialize_grid(STRATEGY_SET,size = grid_size, perc_filled_sites = perc_filled_sites)
        
        grid = PG.make_grid(strategies_init)



    def testExpell(self):
        self.initVariables()
        global s
        for s in [0.5]:
            k=0
            while k<3:
                print "configuration: M=%s, r=%s, q=%s, m=%s, s=%s"%(M,r,q,m,s)
                strategies_init = self.initialize_grid(STRATEGY_SET,size = grid_size, perc_filled_sites = perc_filled_sites)
                strategies,C,strategies_init =  self.simulate2()
                k+=1
        




if __name__ == '__main__':
       
    PG = property_game()
        
    
    '''
    strategies,cooperation,strategies_init = PG.simulate()
    
    grid_init = np.array(strategies_init.values()).reshape([grid_size,grid_size]) 
    print grid_init[0:20,0:20]
    
    print "\n"
    grid = np.array(strategies.values()).reshape([grid_size,grid_size])    
    print grid[0:20,0:20]
    '''
    
