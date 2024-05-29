### IMPORT SECTION
import os
import random

import numpy
import pandas
from datetime import datetime, timezone
from github import Github, GithubException
import time
from requests.exceptions import Timeout

import Settings as cfg


# ### MODULE FUNCTIONS
# def waitRateLimit(ghub):
#     exception_thrown = True
#     while (exception_thrown):
#         exception_thrown = False
#         try:
#             search_limit = ghub.get_rate_limit().search.remaining
#             core_limit = ghub.get_rate_limit().core.remaining

#             S_reset = ghub.get_rate_limit().search.reset
#             ttw = 0
#             now = datetime.now(timezone.utc)
#             if (search_limit <= 5):
#                 S_reset = ghub.get_rate_limit().search.reset
#                 #ttw = (S_reset - now).total_seconds() + 300
#                 ttw = 3600
#                 print('Waiting {} for limit reset', ttw)
#             if (core_limit <= 500):
#                 C_reset = ghub.get_rate_limit().core.reset
#                 #ttw = (C_reset - now).total_seconds() + 300
#                 ttw = 3600
#                 print('Waiting {} for limit reset', ttw)
#             time.sleep(ttw)### originally ttw. Setting 1 hour for testing exceptions
#         except GithubException as ghe:
#             print('Exception Occurred While Getting Rate Limits: Github', ghe)
#             exception_thrown = True
#             pass
#         except Timeout as toe:
#             print('Exception Occurred While Getting Rate Limits: Timeout', toe)
#             exception_thrown = True
#             pass
#         except:
#             print('Execution Interrupted: Unknown Reason')
#             raise

# modified by @bateman to handle multiple tokens and reduce the waiting time
def waitRateLimit(ghub, last_token=None):
    new_token = last_token
    while True:
        try:
            new_token = getRandomToken(last_token)
            ghub = Github(new_token)
            search_limit = ghub.get_rate_limit().search.remaining
            core_limit = ghub.get_rate_limit().core.remaining

            if (search_limit > 5) and (core_limit > 500):
                return ghub, new_token
            else:
                print('Token close to depletion, finding another one')
        except GithubException as ghe:
            print('Exception Occurred While Getting Rate Limits: Github', ghe)

def getReposList():
    """Return the repos name list at the chosen index."""
    filename = cfg.repos_file# "Resources/repositories.txt"
    with open(os.path.join(os.path.dirname(__file__), filename)) as rf:
        reposNameList = rf.readlines()
    reposNameList = [repoName.strip() for repoName in reposNameList] # Remove whitespace characters like `\n` at the end of each line
    return reposNameList

def getRepo(index):
    """Return the repo name at the chosen index. Index ranges (1-N)"""
    reposList = getReposList()
    repo = reposList[index-1]
    return repo

def getTokensList():
    """Return the tokens list"""
    filename = cfg.tokens_file
    with open(filename) as rf:
        tokensList = rf.readlines()
    tokensList = [token.strip() for token in tokensList] # Remove whitespace characters like `\n` at the end of each line
    return tokensList

def getToken(index):
    """Return the token the chosen index. Index ranges (1-N)"""
    tokensList = getTokensList()
    token = tokensList[index - 1]
    return token

def getRandomToken(last_token=None):
    """Return a random token from the tokens list"""
    tokensList = getTokensList()
    if last_token:
        tokensList = [token for token in tokensList if token != last_token]
    token = random.choice(tokensList)
    return token

def add(dataframe, row):
    """Adds a row to the tail of a dataframe"""
    dataframe.loc[-1] = row  # adding a row
    dataframe.index = dataframe.index + 1  # shifting index
    dataframe.sort_index(inplace=True)
    dataframe.iloc[::-1]

def daysBetween(d1, d2):
    """Returns the number of days between two dates"""
    from datetime import datetime
    d1 = datetime.strptime(d1, "%Y-%m-%d")
    d2 = datetime.strptime(d2, "%Y-%m-%d")
    return abs((d2 - d1).days)

def getLastPageRead(log_file):
    """Reads the last read results page during the commit extraction"""
    with open(log_file,'r') as reader:
        log_line = reader.readline()
    lp=int(log_line.split(':')[-1])
    return lp

def getLastActivitiesPageRead(log_file):
    """Reads the last read results page during the activities extraction"""
    with open(log_file,'r') as reader:
        last_line = reader.readline()
    split_string=last_line.split(',')
    last_issues_page=int(split_string[0].split(':')[-1])
    last_issue=split_string[1].split(':')[-1]
    last_item_page=int(split_string[2].split(':')[-1])
    return last_issues_page, last_issue, last_item_page

def daterange(start_date, end_date):
    """Iterates on the dates in a range"""
    from datetime import timedelta  # , date
    from datetime import datetime

    # Fix: add %z to the datetime.strptime to avoid the following error:
    # "ValueError: unconverted data remains: +00:00"
    if type(start_date) == str:
        start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S%z')
    if type(end_date) == str:
        end_date = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S%z')

    for n in range(int((end_date - start_date).days + 2)):
        yield start_date + timedelta(n)

def getFarOutThreshold(values):
    ''' NOT USED FUNCTION'''
    q_3rd = numpy.percentile(values,75)
    q_1st = numpy.percentile(values,25)
    iqr = q_3rd-q_1st
    th = q_3rd + 3*iqr
    return th

def parse_TF_results(results_folder, destination_folder):
    # Read TF from the Reports Folder
    tf_report = open(os.path.join(results_folder,'TF_report.txt'), 'r', encoding="utf8")

    record = False
    for line in tf_report:
        if (record == True):
            dev = line.replace('\n', '').split(';')
            if (len(dev) == 3):
                add(TF_devs, dev)
        if (line.startswith('TF = ')):
            TF_header = tf_report.readline().replace('TF authors (', '').replace('):\n', '').split(';')
            TF_devs = pandas.DataFrame(columns=TF_header)
            record = True
    print(TF_devs)
    TF_devs.to_csv(os.path.join(destination_folder,'TF_devs_names.csv'),
                   sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')

def map_name_login(results_folder, repo_name, destination_folder):
    # Find TF login from Names
    TF_devs = pandas.read_csv(os.path.join(results_folder,'TF_devs_names.csv'), sep=cfg.CSV_separator)
    TF_names_list = TF_devs.Developer.tolist()
    TF_name_login_map = pandas.DataFrame(columns=['name', 'login'])

    token = 'Insert a Valid Token'
    g = Github(token)

    repo = g.get_repo(repo_name)
    contributors = repo.get_contributors()

    for contributor in contributors:
        dev_name = contributor.name
        for name in TF_names_list:
            if (dev_name == name):
                add(TF_name_login_map, [name, contributor.login])
        if (len(TF_name_login_map) == len(TF_names_list)):
            break;
    TF_name_login_map.to_csv(os.path.join(destination_folder,'TF_devs.csv'),
                             sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')

def unmask_TF_routine():
    repos = getReposList()
    for r in repos:
        working_folder = os.path.join(cfg.main_folder, cfg.TF_report_folder,r)
        if ('TF_devs_names.csv' not in os.listdir(working_folder)):
            parse_TF_results(working_folder, working_folder)
        if ('TF_devs.csv' not in os.listdir(working_folder)):
            map_name_login(working_folder,r,working_folder)

def checkTFCoverage(projectName, devs):
    ''' Checks for the given project, the % of TFs in the given devs list '''
    TFfolder = os.path.join(cfg.TF_report_folder.split('/')[1], projectName)
    TFs_file = os.path.join(TFfolder, cfg.TF_developers_file)

    TFs = pandas.read_csv(TFs_file, sep=cfg.CSV_separator)['login'].tolist()
    TFs = [d.lower() for d in TFs]
    num_TFs = len(TFs)

    devs = [d.lower() for d in devs]
    num_devs = len(devs)

    intersection = len(set(TFs).intersection(set(devs)))
    perc = (intersection/num_TFs) * 100

    return num_TFs, num_devs, perc

### MAIN FUNCTION
def main():
    print("Utilities Activated")
#    reposList = getReposList()
#    for gitRepoName in reposList:
#        organization, project = gitRepoName.split('/')
#        devs_file = os.path.join(cfg.A80api_report_folder.split('/')[1], project, cfg.A80api_developers_file)
#        devs = pandas.read_csv(devs_file, sep=cfg.CSV_separator)['login'].tolist()
#
#        TFs, DVS, INTR = checkTFCoverage(project, devs)
#        print('Project: {}, TFs: {}, A80API: {}, TF in A80API: {}'.format(project, TFs, DVS, INTR))

if __name__ == "__main__":
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    os.chdir(THIS_FOLDER)

    main()

