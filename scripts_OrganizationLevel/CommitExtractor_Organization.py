import utilities_Organization as util
import pandas, csv, os, logging
import config_Organization as cfg
from github import Github
import github
from datetime import datetime

def writeCommitFile_Login(gith, project_url, start_date, end_date, path):
    import os, requests
    
    logger = open(path+'/commits_extraction.log','a+')
    
    exception_thrown = True
    while(exception_thrown):
        exception_thrown = False
                            
        cfg.waitRateLimit(gith)
        repo = gith.get_repo(project_url)
        
        commits = repo.get_commits(since=start_date, until=end_date) #Fake users to be filtered out (author_id NOT IN (SELECT id from users where fake=1))
        try:
            num_items = commits.totalCount
        except:
            print('Failed to get commits from this project (Probably Empty): '+project_url)
            return
        last_page = int(num_items/cfg.items_per_page)
        last_page_read=0
        
        if 'commits_raw_login.csv' in os.listdir(path):
            commits_data = pandas.read_csv(path+'/commits_raw_login.csv', sep=',')
            last_page_read = util.get_last_page_read_short(path+'/commits_extraction.log')
        else:
            commits_data=pandas.DataFrame(columns=['sha', 'author_id', 'date'])
        
        if 'excluded_for_NoneType.csv' in os.listdir(path):
            excluded_commits = pandas.read_csv(path+'/excluded_for_NoneType.csv', sep=',')
        else:
            excluded_commits=pandas.DataFrame(columns=['sha'])
        
        try:
            for page in range(last_page_read, last_page+1):
                commits_page = commits.get_page(page)
                for commit in commits_page:
                    cfg.waitRateLimit(gith)
                    sha=commit.sha
                    if((sha not in commits_data.sha.tolist()) & (sha not in excluded_commits.sha.tolist())):
                        if(commit.author): ### If author is NoneType, that means the author is no longer active in GitHub
                            cfg.waitRateLimit(gith)
                            author_id=commit.author.login ### HERE IS THE DIFFERENCE
                            date=commit.commit.author.date
                            util.add(commits_data,[sha, author_id, date])
            if(len(commits_data)>0):
                commits_data.to_csv(path+'/commits_raw_login.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
        except github.GithubException:
            print('Exception Occurred While Getting COMMITS: Github')
            if(len(commits_data)>0):
                commits_data.to_csv(path+'/commits_raw_login.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
            logger.write('last_page:{}\n'.format(page))
            logger.flush()
            exception_thrown = True
            pass
        except requests.exceptions.Timeout:
            print('Exception Occurred While Getting COMMITS: Timeout')
            if(len(commits_data)>0):
                commits_data.to_csv(path+'/commits_raw_login.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
            logger.write('last_page:{}\n'.format(page))
            logger.flush()
            exception_thrown = True
            pass
        except AttributeError:
            print('Exception Occurred While Getting COMMIT DATA: NoneType for Author. SHA: '+sha)
            util.add(excluded_commits, [sha])
            if(len(commits_data)>0):
                commits_data.to_csv(path+'/commits_raw_login.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
            excluded_commits.to_csv(path+'/excluded_for_NoneType.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
            logger.write('last_page:{}\n'.format(page))
            logger.flush()
            exception_thrown = True
        except:
            print('Execution Interrupted While Getting COMMITS')
            if(len(commits_data)>0):
                commits_data.to_csv(path+'/commits_raw_login.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
            logger.write('last_page:{}\n'.format(page))
            logger.flush()
            raise

def writeCommitTable_Login(commits_data):
    # GET MIN and MAX COMMIT DATETIME
    max_commit_date=max(commits_data['date'])
    min_commit_date=min(commits_data['date'])

    column_names=['user_id']
    for single_date in util.daterange(min_commit_date, max_commit_date): #daterange(min_commit_date, max_commit_date):
        column_names.append(single_date.strftime("%Y-%m-%d"))

    # ITERATE UNIQUE USERS (U)
    u_data=[]
    for u in commits_data.author_id.unique():
        user_id=u
        cur_user_data=[user_id]
        date_commit_count = pandas.to_datetime(commits_data[['date']][commits_data['author_id']==u].pop('date'), format="%Y-%m-%d").dt.date.value_counts()
        # ITERATE FROM DAY1 --> DAYN (D)
        for d in column_names[1:]:
            # IF U COMMITTED DURING D THEN U[D]=1 ELSE U(D)=0
            try:
                cur_user_data.append(date_commit_count[pandas.to_datetime(d).date()])
            except Exception: # add "as name_given_to_exception" before ":" to get info 
                cur_user_data.append(0)
        #print("finished user", u)
        u_data.append(cur_user_data)
    
    commit_table=pandas.DataFrame(u_data,columns=column_names)
    commit_table.to_csv(super_path+'/'+project_name+'/commit_table_login.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
    print("Commit CSV Written: ", project_name)
    
def writeIntervalsBreaks_Files(commit_table):
    # Calcola days between commits, if commits are in adjacent days count 1
    inactivity_intervals_data=[]
    break_dates=[]
    for index, u in commit_table.iterrows():
        row = [u[0]] #User_id
        current_break_dates = [u[0]] #User_id
        commit_dates=[]
        for i in range(1,len(u)):
            if(u[i]>0):
                commit_dates.append(commit_table.columns[i])
        for i in range(0,len(commit_dates)-1):
            period=util.days_between(commit_dates[i], commit_dates[i+1])
            if(period>1):
                row.append(period)
                current_break_dates.append(commit_dates[i]+"/"+commit_dates[i+1])
        #print('Last User Done: ', row[0])
        inactivity_intervals_data.append(row)
        break_dates.append(current_break_dates)
        user_lifespan = util.days_between(commit_dates[0], commit_dates[len(commit_dates)-1])+1
        commit_frequency = len(commit_dates)/user_lifespan
        row.append(user_lifespan)
        row.append(commit_frequency)
    print('Inactivity Computation Done: ', project_name)
    
    with open(super_path+'/'+project_name+'/inactivity_interval_list.csv', 'w', newline='') as outcsv:   
        #configure writer to write standard csv file
        writer = csv.writer(outcsv, quoting=csv.QUOTE_NONE, quotechar='"',escapechar='\\')
        for r in inactivity_intervals_data:
            #Write item to outcsv
            writer.writerow(r)
    
    with open(super_path+'/'+project_name+'/break_dates_list.csv', 'w', newline='') as outcsv:   
        #configure writer to write standard csv file
        writer = csv.writer(outcsv, quoting=csv.QUOTE_NONE, quotechar='"',escapechar='\\')
        for r in break_dates:
            #Write item to outcsv
            writer.writerow(r)
    logging.info('Project: '+project_name+' DONE')


    
token_index=6
tm = cfg.TokenManagement.getInstance()
g = Github(tm.getToken(token_index))
g.per_page=cfg.items_per_page

p_names = cfg.p_names
organizations = cfg.organizations

chosen_organization=organizations[token_index-1]
main_project=p_names[token_index-1]
super_path = cfg.super_path + '/' + chosen_organization
os.makedirs(super_path, exist_ok=True)  
org = g.get_organization(chosen_organization)

org_repos = org.get_repos(type='all')

for repo in org_repos:
    cfg.waitRateLimit(g)
    project_name = repo.name
    if project_name != main_project:
        logging.basicConfig(filename=super_path+'/CommitExtraction_Organization.log',level=logging.INFO)
        logging.info('Project: '+project_name+' Org: '+chosen_organization+' Started')
    
        cfg.waitRateLimit(g)
        project_start_dt=repo.created_at
        project_start=project_start_dt.strftime('%Y-%m-%d %H:%M:%S')
    
        path = (super_path+'/'+project_name)
        os.makedirs(path, exist_ok=True)  
        
        collection_day=datetime.strptime(cfg.collection_date, '%Y-%m-%d')
        cfg.waitRateLimit(g)
        project_url = chosen_organization+'/'+project_name 
        
        writeCommitFile_Login(g, project_url, project_start_dt, collection_day, path)
        #writeCommitFile_Basic(commits, path)
        if 'commits_raw_login.csv' in os.listdir(path):
            commits_data = pandas.read_csv(path+'/commits_raw_login.csv', sep=',')
            writeCommitTable_Login(commits_data)
        
        if 'commit_table_login.csv' in os.listdir(path):
            commit_table = pandas.read_csv(path+'/commit_table_login.csv', sep=',')
            writeIntervalsBreaks_Files(commit_table)

print('Side Projects Extraction COMPLETE!!!')