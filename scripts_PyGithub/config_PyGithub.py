# -*- coding: utf-8 -*-
"""
Created on Thu Apr 18 11:39:55 2019

@author: Pepp_
"""
from github import Github

p_names=['jabref','ionic','atom','flutter','linguist','elixir','react','framework','node','rails']
p_urls=['JabRef/jabref','ionic-team/ionic','atom/atom','flutter/flutter','github/linguist','elixir-lang/elixir','facebook/react','laravel/framework','nodejs/node','rails/rails']
collection_date='2019-06-20'

dead_threshold = 365

items_per_page=100

super_path = '../PyGithub'

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
        
def waitRateLimit(github):
    from datetime import datetime
    import time
    
    search_limit = github.get_rate_limit().search.remaining
    core_limit = github.get_rate_limit().core.remaining
    
    S_reset=github.get_rate_limit().search.reset
    ttw=0
    now=datetime.utcnow()
    if(search_limit<=5):
        S_reset=github.get_rate_limit().search.reset
        ttw = (S_reset-now).total_seconds() + 10
        print('Waiting {} for limit reset', ttw)
    if(core_limit<=500):
        C_reset=github.get_rate_limit().core.reset
        ttw = (C_reset-now).total_seconds() + 100
        print('Waiting {} for limit reset', ttw)
    time.sleep(ttw)
    