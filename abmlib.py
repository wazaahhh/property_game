import numpy as np
from random import choice,randrange, shuffle
import time
from datetime import datetime
import json,simplejson


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
    



            '''nghbs = self.search_for_sites(site,strategies,site_occupation="empty")
            o_site = site.copy()
            site = nghbs[np.random.randint(len(nghbs))] 
            #print "new site : %s (strategy : %s)"%(site,strategies[site])
            #pay_off = self.pay_off(site,strategies)
            chgDic = {'best_pay_off': 0, 'best_site': site, 'o_pay_off': 1.5, 'o_site': o_site }
            strategies = self.move(chgDic,strategies)['strategies']
            #print "new site : %s (strategy : %s)"%(site,strategies[site])
            comparison = self.play_with_all_neighbors(site,strategies)
            '''
            
            
            
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
         
         
         
                 
        '''#T,R,P,S = (1.0,1.0,0.0,0.0) # cooperators = 0.6
        #T,R,P,S = (1.05,1.0,0.0,0.0) # cooperators = 0.1 (found approx. 0.45)
        #T,R,P,S = (1.1,1.0,0.0,0.0) # cooperators = 0.0 (found approx. 0.27)
        #T,R,P,S = (1.2,1.0,0.0,0.0) # cooperators = 0.0 (found approx. 0.25)
        #T,R,P,S = (1.3,1.0,0.0,0.0) # cooperators = 0.0 (found approx. 0.19)
        #T,R,P,S = (1.7,1.0,0.0,0.0) # cooperators = 0.0 (found approx. 0.13)
        '''
            
            
                '''
    strategies,cooperation,strategies_init = PG.simulate()
    
    grid_init = np.array(strategies_init.values()).reshape([grid_size,grid_size]) 
    print grid_init[0:20,0:20]
    
    print "\n"
    grid = np.array(strategies.values()).reshape([grid_size,grid_size])    
    print grid[0:20,0:20]
    '''
    
    
    def simulate2(self,verbose=0):
        
        init_timestamp = datetime.now() 
        init_T = time.mktime(init_timestamp.timetuple())
       
        
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

        J = json.dumps(dic)
        key = bucket.new_key("results/json/simul%s_grid%s_%s_r%s_q%s_m%s_s%s_M%s.json"%(iterations,grid_size,datetime.strftime(init_timestamp,'%Y%m%d%H%M%S'),r,q,m,s,M))
        key.set_contents_from_string(J)
        
            
        return dic
 


    def initVariables(self):
        
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
        
        grid = self.make_grid(strategies_init)



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
        



