from matplotlib import use, get_backend
if 'Agg' != get_backend().title(): 
    use('Agg')

import numpy as np
import pylab as pl
from random import choice,randrange, shuffle
import time

class property_game():

    def __init__(self):
        self.iconn = None
        self.sconn = None
    
    
    def initialize_grid(self,STRATEGY_SET,size=100,perc_filled_sites=1):
        '''initialize grid'''

        l = size**2

        shuffle_grid = np.arange(l)        
        shuffle(shuffle_grid)
        
        
        
        if perc_filled_sites < 1:
            ''' select randomly sites out of grid in proportion of perc_filled_site'''
            max = round(perc_filled_sites*l)
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
        
        values  = []
        for key in sorted(strategies):
            values.append(strategies[key])
        
        grid = np.array(values).reshape([grid_size,grid_size])    
        return grid


    def crop_grid(self,site,strategies):
           
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
        
   
#     def play_with_one_neighbour(self,player_1,strategies,update=False):
#     
#  
#         '''find neighbors (non empty sites)'''        
#         nghbs_1 = self.find_neighbors(strategies,player_1)
# 
#         '''randomly select a neighbor'''
#         player_2 = choice(nghbs_1)
# 
#         ''' player_1 and player_2 play Prisoners' dilemma together'''
#                 
#         pay_off_1,pay_off_2 = self.prisoners_dilemma(player_1,player_2,strategies)
#     
#         ''' player_1 plays with all neighbors '''
#         #pay_off_1 = []
#         
#         #for i,ix in enumerate(nghbs_1):
#         #    pay_off_1.append(self.prisoners_dilemma(player_1,ix,strategies)[0])
#         #pay_off_1 = np.sum(pay_off_1)
#     
#         ''' player_2 plays with all neighbors '''
#         #nghbs_2 = self.find_neighbors(strategies,player_2)
#         #print nghbs_2
# 
#         #pay_off_2 = []
#     
#         #for i,ix in enumerate(nghbs_2):
#         #    pay_off_2.append(self.prisoners_dilemma(player_2,ix,strategies)[0])
#         #pay_off_2 = np.sum(pay_off_2)
# 
# 
#         pay_offs= {player_1:pay_off_1,player_2:pay_off_2}
#     
#         if strategies[player_1]!=strategies[player_2] and update==True:
#             '''update strategy with some probability'''
#             #print player_1,player_2
#             #print "old strategy: ", strategies[player_1],strategies[player_2]
#             self.update_strategy_Fermi(player_1,player_2,pay_offs,strategies) 
#             #print "update :" , strategies[player_1],strategies[player_2]
#          
#         return strategies,pay_offs


    def play_with_all_neighbors(self,player_1,strategies):
        '''play simulateneously with all neighbors'''
        
        '''find neighbors (non empty sites)'''  
        if isinstance(player_1,int) or isinstance(player_1,float):
            nghbs_1 = self.find_neighbors(player_1,strategies)
        elif len(player_1) == 2:
            nghbs_1 = self.find_neighbors(player_1[0],strategies)
            
        #print nghbs_1
        pay_off = []

        for i,ix in enumerate(nghbs_1):
            p1 = self.prisoners_dilemma(player_1,ix,strategies)[0]
            pay_off = np.append(pay_off,p1)
            
        pay_off = np.sum(pay_off)
        
        
        return pay_off

    def compare_payoffs_with_random_neighbor(self,player_1,strategies):
     
        pay_off_1 = self.play_with_all_neighbors(player_1, strategies)
        
        '''find neighbors (non empty sites)'''
        
        #print "looking for neighbors"
        #print player_1, strategies[player_1]
        
        nghbs_1 = self.find_neighbors(player_1,strategies)
        
        '''randomly select a neighbor'''
        if len(nghbs_1)>0:
            player_2 = choice(nghbs_1)
        #except:
        #    print "no neighbor"
        #    return {'strategies' : strategies}
        else:
            print "no neighbor"
            #print player_1, strategies[player_1]
            #print nghbs_1
            #self.crop_grid(player_1,strategies)
            #time.sleep(0.5)
            #print A
            return {'strategies' : strategies}
            
        pay_off_2 = self.play_with_all_neighbors(player_2, strategies)    
        pay_offs= {player_1:pay_off_1,player_2:pay_off_2}
             
        return {'strategies' : strategies,'player_1':player_1,'player_2':player_2,'pay_offs' : pay_offs} 
         
#     def update_strategy_simple(self,player_1,strategies,r=0.05):
#         '''calculate pay-off of neighbors and update player_1 strategy to the strategy of most performing neighbor'''
#     
# 
#         '''find neighbors (non empty sites)'''        
#         nghbs_1 = self.find_neighbors(strategies,player_1)
# 
#         ''' each neighbor of player_1 with own neighbors'''
#         pay_off_nghbs_1 = {}
#         
#         for i,ix in enumerate(nghbs_1):
#             pay_off_nghbs_1[ix]= self.play_with_all_neighbors(player_1,strategies,update=False)
#         
#         
#         #print pay_off_nghbs_1
#         
#         if len(pay_off_nghbs_1)==0:
#             return strategies
#         
#         ''' find best performing neighbor '''
#         
#         player_max = max(pay_off_nghbs_1, key=pay_off_nghbs_1.get)
#         
#         '''update strategy of player_1 '''
#         
#         rand = np.random.rand()
#         
#         if rand > r:
#             strategies[player_1]=strategies[player_max]
#         
#         return strategies
#         

    def update_strategy_Fermi(self,player_1,player_2,pay_offs,strategies,K=0.1):
        '''update strategies by player 1 trying to reproduce the strategy of player 2'''
           
                
        '''Fermi Temperature'''
        W =  1/(1+np.exp((pay_offs[player_1]-pay_offs[player_2])/K))
        rand = np.random.rand()
        
        print "%.2f,%.2f"%(rand,W)

        if rand < W and strategies[player_1] <> strategies[player_2]:
            old_str = strategies[player_1]
            strategies[player_1]=strategies[player_2]
            print "update : %s => %s" %(old_str,strategies[player_1])

        return strategies



    def noise_1(self,q):
        '''cooperate with probability q or defect with probability 1-q'''

        rand = np.random.rand()
        
        if rand < q:
            return 1
        else:
            return 0
 
    def find_neighbors(self,site,strategies,non_empty_sites=True):
        '''find neighbors'''
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

    def search_for_sites(self,site,strategies,site_occupation="all",plot=False):
            '''search for empty site with better pay-off within the (2M + 1) x (2M + 1) Moore's neighborhood '''
            ''' options for occupation : 'all','occupied','empty' '''
            #kwargs =
            
            
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
            
            
            if site_occupation == 'occupied':
                delete = []
                for i,ix in enumerate(nghbs):
                    if strategies[ix] < 0:
                        delete.append(i)
                        
                nghbs = np.delete(nghbs,delete)
                
            if site_occupation == 'empty':
                delete = []
                for i,ix in enumerate(nghbs):
                    if strategies[ix] > -1:
                        delete.append(i)
                
                nghbs = np.delete(nghbs,delete)

            if plot :
                print "blah"
            
            return nghbs
        
        
    def explore_neighborhood(self,site,strategies,site_occupation="all",forceMove=False,plot=False):
        '''Find neighboring sites with with better pay-off'''
    
        #print "M=%s"%1
        
        neighbor_sites = self.search_for_sites(site,strategies,site_occupation=site_occupation)
    
        #print neighbor_sites
        
        
        pay_off = {}

        #print site,strategies[site]

    
        if not strategies[site]==-1:
            ownPayOff = self.play_with_all_neighbors(site,strategies)
            pay_off[site] = ownPayOff
        else:
            print "no strategy at this site"
            return 0
    
        if forceMove:
            pay_off.pop(site)
    
    
        for i,ix in enumerate(neighbor_sites):
            
            #print ix,strategies[ix]
            
            if strategies[ix] == -1:
                pay_off[ix] = self.play_with_all_neighbors([ix,strategies[site]],strategies)
            else: 
                pay_off[ix] = self.play_with_all_neighbors(ix,strategies)
            
            pay_off[ix] = pay_off[ix] + (np.random.rand()-0.5)/10000.
        
        best_site = max(pay_off, key=pay_off.get)
        
        #print site,pay_off[site]
        #print best_site,pay_off[best_site]
        return {'o_site': int(site), 'o_pay_off' :np.round(ownPayOff,4), 'best_site':int(best_site), 'best_payoff' : np.round(pay_off[best_site],4) }

  
    def moveToBestEmptySite(self,player_1,strategies,plot=False):
        
            
        self.crop_grid(player_1, strategies)
        
        BestEmptySite = self.explore_neighborhood(player_1,strategies,site_occupation="empty")
    
        rand = np.random.rand()
    
        if BestEmptySite == 0:
            pass
    
        elif BestEmptySite['best_site'] == BestEmptySite['o_site']:
            print "already best position"
            
        elif rand <= s_MoveEmpty:
            strategies[BestEmptySite['best_site']] = strategies[BestEmptySite['o_site']]
            strategies[BestEmptySite['o_site']] = -1
            print "player %s taking best empty place %s"%(player_1,BestEmptySite['best_site'])
            self.crop_grid(player_1, strategies)
    
        return strategies
    
    def moveExpell(self,player_1,strategies,plot=False):
        
        if plot:
            print "original configuration"
            self.crop_grid(player_1,strategies)
        
        rand = np.random.rand()
        
        BestOccupiedSite = self.explore_neighborhood(player_1,strategies,site_occupation="occupied")
        print BestOccupiedSite
        
        if BestOccupiedSite == 0:
            print "no strategy on this site"
            pass
        
        elif BestOccupiedSite['best_site'] == BestOccupiedSite['o_site']:
            print "already best position"
        
        elif rand <= s_MoveExpell:
            print "player %s taking place of player %s"%(player_1,BestOccupiedSite['best_site'])
            
            expelledStrategy = strategies[BestOccupiedSite['best_site']]
            
            strategies[BestOccupiedSite['best_site']] = strategies[BestOccupiedSite['o_site']]  
            strategies[BestOccupiedSite['o_site']] = -1

            if plot:
                self.crop_grid(player_1, strategies)

            '''search empty site for expelled player'''
             
            print "search empty site for expelled player %s"%BestOccupiedSite['best_site']
            
            if plot:
                self.crop_grid(BestOccupiedSite['best_site'], strategies)
            
            BestEmptySite = self.explore_neighborhood(BestOccupiedSite['best_site'],strategies,site_occupation="empty",forceMove = True,plot=True)
            #print BestEmptySite
            
            print "found new site for %s => %s"%(BestOccupiedSite['best_site'],BestEmptySite['best_site'])
            strategies[BestEmptySite['best_site']] = expelledStrategy
            #strategies[BestEmptySite['o_site']] = -1
            
            
            if plot:
                self.crop_grid(BestOccupiedSite['best_site'], strategies)
            
            #print "player %s taking best empty place %s"%(player_1,)  
        return strategies 
                  
            


    def simulate(self,update=True,mobility=True,plot=True):
        
        #print strategies
        #strategies_init = strategies.copy()
        strategies = strategies_init.copy()
        
        coop = np.array(strategies.values())
        empty = len(coop[coop==-1])
        
        cooperation = []
        
        for i in range(MCS):
            '''pick an agent randomly'''
            player_1 = choice(strategies.keys())
            
            print '\n',i,player_1
            
            if strategies[player_1]==-1:
                try:
                    cooperation.append(cooperation[-1])
                except:
                    cooperation.append(0)
                continue
            
            
            comparison = self.compare_payoffs_with_random_neighbor(player_1,strategies)
                     
            if comparison.has_key('player_1'):
                if update:
                    print "update : %s"%player_1
                    strategies = self.update_strategy_Fermi(comparison['player_1'], comparison['player_2'], comparison['pay_offs'], strategies)
                
                if s_MoveEmpty > 0:
                    print "move to Best Empty Site : %s"%player_1
                    strategies = self.moveToBestEmptySite(player_1,strategies,plot=False)
            
                if s_MoveExpell > 0:
                    print "move to Expell : %s"%player_1
                    strategies = self.moveExpell(player_1,strategies,plot=False)
                    
                    coop = np.array(strategies.values())
                    check_empty = len(coop[coop==-1])
                    
                    if not empty == check_empty:
                        print empty,check_empty
                        time.sleep(2)
                    
            
            coop = np.array(strategies.values())
            
            cooperation.append(np.sum(coop[coop>0])/float(len(coop)))
            
            print "cooperation level : %.2f percent"%cooperation[-1]
        
            
        
            if sum(coop[coop>-1])==0:
                print "no cooperator left"
                break
        
        print "empty_sites : %s" %len(coop[coop==-1])
        print "defectors : %s" %len(coop[coop==0])
        print "cooperators : %s"%len(coop[coop==1])
        
        
        if plot:
            pl.figure(1)
            pl.plot(cooperation,'-')
            pl.xlabel("Monte Carlo Steps (MCS)")
            pl.ylabel("proportion of cooperators")
            pl.savefig("cooperation.png")
            pl.close()
        
        return strategies,cooperation,strategies_init


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

if __name__ == '__main__':
    PG = property_game()

    
    global perc_filled_sites
    perc_filled_sites = 0.50

    global STRATEGY_SET
    STRATEGY_SET = {'C':1,'D':0}

    global grid_size
    grid_size = 49
    
    iterations = 100
    global MCS
    MCS = (grid_size**2)*iterations # Monte Carlo Steps

    global site_occupation  # decide which sites to search for
    site_occupation = "all" #("all","empty","occupied")

    global M #Moore's Distance
    M = 5
 
    global s_MoveEmpty
    s_MoveEmpty = 0.

    global s_MoveExpell
    s_MoveExpell = 0.2

    global strategies_init
    strategies_init = PG.initialize_grid(STRATEGY_SET,size = grid_size, perc_filled_sites = perc_filled_sites)
    
    #global strategies 
    #strategies = strategies_init.copy()
    
    grid = PG.make_grid(strategies_init)
    
    '''
    strategies,cooperation,strategies_init = PG.simulate()
    
    grid_init = np.array(strategies_init.values()).reshape([grid_size,grid_size]) 
    print grid_init[0:20,0:20]
    
    print "\n"
    grid = np.array(strategies.values()).reshape([grid_size,grid_size])    
    print grid[0:20,0:20]
    '''
    
