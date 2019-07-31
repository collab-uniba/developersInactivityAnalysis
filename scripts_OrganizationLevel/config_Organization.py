from github import Github
from datetime import datetime
import time, requests, github

items_per_page=100

p_names = ['jabref','ionic','flutter','atom','linguist','elixir','react','framework','node','rails']
organizations = ['JabRef','ionic-team','flutter','atom','github','elixir-lang','facebook','laravel','nodejs','rails']

key_folders=['Activities_Plots','Dead&Resurrected_Users','Hibernated&Unfrozen_Users','Sleeping&Awaken_Users','DevStats_Plots','Longer_Breaks']
collection_date='2019-06-20'

dead_threshold = 365

super_path = '../Organization'

class TokenManagement:
    from github import Github

    __instance = None
             
    token_file='tokens.txt'    
    
    tf = open(token_file, 'r')
    tl = tf.readlines()
    tokens=len(tl)
    token=''
    #tl=[]
    #tokens=0
    
    @staticmethod 
    def getInstance():
        """ Static access method. """
        if TokenManagement.__instance == None:
            TokenManagement()
        return TokenManagement.__instance
  
    def __init__(self):
        """ Virtually private constructor. """
        if TokenManagement.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            TokenManagement.__instance = self

    def newToken(self):
        if(self.tokens==0):
            tf = open(self.token_file, 'r')
            self.tl = tf.readlines()
            self.tokens=len(self.tl)
            self.token=self.tl.pop().rstrip('\n\r')
        self.tokens-=1
        return self.token
    
    def getToken(self, index):
        if(index>self.tokens):
            print("Token Not Available for Index", index)
        else:
            self.token=self.tl.pop(index-1).rstrip('\n\r')
            self.tokens-=1
        return self.token

def checkRateLimit(github):
    tm=TokenManagement.getInstance()
    search_limit = github.get_rate_limit().search.remaining
    core_limit = github.get_rate_limit().core.remaining
    if(search_limit<=5) | (core_limit<=500):
        nt=tm.newToken()
        print('Changing Token t: {}, S_lmt: {}, C_lmt: {}', nt, search_limit, core_limit)
        github = Github(nt)
        github.per_page=items_per_page
        checkRateLimit(github)
        
def waitRateLimit(ghub):
    exception_thrown = True
    while(exception_thrown):
        exception_thrown = False
        try:
            search_limit = ghub.get_rate_limit().search.remaining
            core_limit = ghub.get_rate_limit().core.remaining
            
            S_reset=ghub.get_rate_limit().search.reset
            ttw=0
            now=datetime.utcnow()
            if(search_limit<=5):
                S_reset=ghub.get_rate_limit().search.reset
                ttw = (S_reset-now).total_seconds() + 10
                print('Waiting {} for limit reset', ttw)
            if(core_limit<=500):
                C_reset=ghub.get_rate_limit().core.reset
                ttw = (C_reset-now).total_seconds() + 100
                print('Waiting {} for limit reset', ttw)
            time.sleep(ttw)
        except github.GithubException as ghe:
            print('Exception Occurred While Getting Rate Limits: Github', ghe)
            exception_thrown=True
            pass
        except requests.exceptions.Timeout:
            print('Exception Occurred While Getting Rate Limits: Timeout', ghe)
            exception_thrown=True
            pass
        except:
            print('Execution Interrupted While Getting Rate Limits', ghe)
            raise
    
    
    