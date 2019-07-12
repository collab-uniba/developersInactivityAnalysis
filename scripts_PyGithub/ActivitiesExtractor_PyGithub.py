### Import Library
import pandas, os, requests
from datetime import datetime#, date
import utilities_PyGithub as util
import config_PyGithub as cfg
from github import Github
import github

#tm = cfg.TokenManagement.getInstance()
#g = Github(tm.newToken())

p_names=cfg.p_names
p_urls=cfg.p_urls

super_path = cfg.super_path
    
def get_last_page_read_short(log_file):
    log_handler = open (log_file,'r')
    log_lines_list = log_handler.readlines()
    log_handler.close()
    last_line=log_lines_list[-1]
    return int(last_line.split(':')[-1])

def get_last_page_read(log_file):
    log_handler = open (log_file,'r')
    log_lines_list = log_handler.readlines()
    log_handler.close()
    if(len(log_lines_list)>0):
        last_line=log_lines_list[-1]
        split_string=last_line.split(',')
        last_issues_page=int(split_string[0].split(':')[-1])
        last_issue=split_string[1].split(':')[-1]
        last_item_page=int(split_string[2].split(':')[-1])
    else:
        last_issues_page=0
        last_issue=''
        last_item_page=0
    return last_issues_page, last_issue, last_item_page

def get_action_timeline(action_name, action_table, column_names):
    cur_action_data=[action_name]
    date_action_count = pandas.to_datetime(action_table[['date']].pop('date'), format="%Y-%m-%d").dt.date.value_counts()
    # ITERATE FROM DAY1 --> DAYN (D)
    for d in column_names[1:]:
        # IF U COMMITTED DURING D THEN U[D]=1 ELSE U(D)=0
        try:
            cur_action_data.append(date_action_count[pandas.to_datetime(d).date()])
        except Exception: # add "as name_given_to_exception" before ":" to get info 
            cur_action_data.append(0)
    return cur_action_data

def get_issues_prs(gith, repo, project_name, start_date, developer_login):
    path = super_path+'/'+project_name+'/Other_Activities/'+developer_login
    os.makedirs(path, exist_ok=True) 
    
    exception_thrown = True
    while(exception_thrown):
        exception_thrown = False
        
        logger = open(path+'/issues_pr_extraction.log','a+')
        ### Get Issue / Pull Requests
        created_issues_prs = repo.get_issues(state='all', sort='created_at', since=start_date, creator=developer_login)
        num_items = created_issues_prs.totalCount
        last_page = int(num_items/cfg.items_per_page)
        last_page_read=0
        
        if 'issues_pr_creation.csv' in os.listdir(path):
            issues_prs_data = pandas.read_csv(path+'/issues_pr_creation.csv', sep=',')
            last_page_read = get_last_page_read_short(path+'/issues_pr_extraction.log')
        else:
            issues_prs_data = pandas.DataFrame(columns=['id','date','creator_login'])
            
        try:
            for page in range(last_page_read, last_page+1):
                created_issues_prs_page = created_issues_prs.get_page(page)
                for issue in created_issues_prs_page:
                    issue_id=issue.id
                    if(issue_id not in issues_prs_data.id.tolist()):
                        if(issue.user):
                            cfg.waitRateLimit(gith)
                            util.add(issues_prs_data, [issue_id, issue.created_at, issue.user.login])
                logger.write('last_page_read:{}\n'.format(page))
                logger.flush()
            if(len(issues_prs_data)>0):
                issues_prs_data.to_csv(path+'/issues_pr_creation.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
            print('{}: Issues/Pulls Extraction Complete'.format(developer_login))
        except github.GithubException:
            print('Exception Occurred While Getting ISSUES/PULLS: Github')
            logger.write('last_page_read:{}\n'.format(page))
            logger.flush()
            if(len(issues_prs_data)>0):
                issues_prs_data.to_csv(path+'/issues_pr_creation.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
            #get_issues_prs(gith, repo, project_name, start_date, developer_login)
            exception_thrown=True
            pass
        except requests.exceptions.Timeout:
            print('Exception Occurred While Getting ISSUES/PULLS: Timeout')
            logger.write('last_page_read:{}\n'.format(page))
            logger.flush()
            if(len(issues_prs_data)>0):
                issues_prs_data.to_csv(path+'/issues_pr_creation.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
            #get_issues_prs(gith, repo, project_name, start_date, developer_login)
            exception_thrown=True
            pass
        except:
            print('Execution Interrupted While Getting ISSUES/PULLS')
            logger.write('last_page_read:{}\n'.format(page))
            logger.flush()
            if(len(issues_prs_data)>0):
                issues_prs_data.to_csv(path+'/issues_pr_creation.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
            raise
            
def get_issues_comments_repo(gith, repo, project_name, start_date, active_users):
    path = super_path+'/'+project_name+'/Other_Activities'
    os.makedirs(path, exist_ok=True)
    
    exception_thrown = True
    while(exception_thrown):
        exception_thrown = False
        
        if 'issues_comments_repo.csv' in os.listdir(path):
            issues_comments_data = pandas.read_csv(path+'/issues_comments_repo.csv', sep=',')
        else:
            issues_comments_data = pandas.DataFrame(columns=['id','date','creator_login'])
        
        if 'issues_comments_extraction.log' in os.listdir(path):
            last_issues_page, last_issue, last_comments_page = get_last_page_read(path+'/issues_comments_extraction.log')
        else:
            last_issues_page=0
            last_issue='' 
            last_comments_page=0
            
        if 'comments_extraction_completed_issues.csv' in os.listdir(path):
            completed_issues = pandas.read_csv(path+'/comments_extraction_completed_issues.csv', sep=',')
        else:
            completed_issues = pandas.DataFrame(columns=['id'])

        logger = open(path+'/issues_comments_extraction.log','a+')
        
        ### Get Comments on Issue
        try:
            issues_page=0
            issue_id=''
            page=0
            
            issues = repo.get_issues(state='all', sort='created_at', since=start_date)
            num_issues = issues.totalCount
            final_issues_page = int(num_issues/cfg.items_per_page)            
            
            for issues_page in range(last_issues_page, final_issues_page+1):
                cfg.waitRateLimit(gith)
                current_issues_page = issues.get_page(issues_page)
                for issue in current_issues_page:
                    cfg.waitRateLimit(gith)
                    issue_id=issue.id
                    if(issue_id not in completed_issues.id.tolist()):
                        if(issue_id!=last_issue):
                            last_page=0
                        else:
                            last_page=last_comments_page
                        cfg.waitRateLimit(gith)
                        issues_comments = issue.get_comments(since=start_date)
                        num_items = issues_comments.totalCount
                        final_page = int(num_items/cfg.items_per_page)        
                        
                        for page in range(last_page, final_page+1):
                            cfg.waitRateLimit(gith)
                            issues_comments_page = issues_comments.get_page(page)
                            for comment in issues_comments_page:
                                cfg.waitRateLimit(gith)
                                comment_id=comment.id
                                if(comment_id not in issues_comments_data.id.tolist()):
                                    if(comment.user):
                                        cfg.waitRateLimit(gith)
                                        user_login=comment.user.login
                                        if(user_login in active_users):
                                            cfg.waitRateLimit(gith)
                                            util.add(issues_comments_data, [comment_id, comment.created_at, user_login])
                        util.add(completed_issues, issue_id)
            if(len(issues_comments_data)>0):
                issues_comments_data.to_csv(path+'/issues_comments_repo.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
                completed_issues.to_csv(path+'/comments_extraction_completed_issues.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
                os.rename(path+'/issues_comments_repo.csv', path+'/complete_issues_comments_repo.csv')
            print('{}: Issues Comments Extraction Complete'.format(repo))
        except github.GithubException:
            print('Exception Occurred While Getting ISSUES COMMENTS: Github')
            logger.write('last_issues_page:{},last_issue:{},last_comment_page:{}\n'.format(issues_page, issue_id, page))
            logger.flush()
            if(len(issues_comments_data)>0):
                issues_comments_data.to_csv(path+'/issues_comments_repo.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
                completed_issues.to_csv(path+'/comments_extraction_completed_issues.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
            exception_thrown=True
            pass
        except requests.exceptions.Timeout:
            print('Exception Occurred While Getting ISSUES COMMENTS: Timeout')
            logger.write('last_issues_page:{},last_issue:{},last_comment_page:{}\n'.format(issues_page, issue_id, page))
            logger.flush()
            if(len(issues_comments_data)>0):
                issues_comments_data.to_csv(path+'/issues_comments_repo.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
                completed_issues.to_csv(path+'/comments_extraction_completed_issues.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
            exception_thrown=True
            pass
        except:
            print('Execution Interrupted While Getting ISSUES COMMENTS')
            logger.write('last_issues_page:{},last_issue:{},last_comment_page:{}\n'.format(issues_page, issue_id, page))
            logger.flush()
            if(len(issues_comments_data)>0):
                issues_comments_data.to_csv(path+'/issues_comments_repo.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
                completed_issues.to_csv(path+'/comments_extraction_completed_issues.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
            raise
            
def get_issues_comments_dev(project_name, developer_login):
    path = super_path+'/'+project_name+'/Other_Activities/'+developer_login
    os.makedirs(path, exist_ok=True) 
    
    ### Get Comments on Issue
    issues_comments = pandas.read_csv(super_path+'/'+project_name+'/Other_Activities/complete_issues_comments_repo.csv', sep=',')
    issues_comments_data = pandas.DataFrame(columns=['id','date','creator_login'])
    
    for index, comment in issues_comments.iterrows():
        if(comment['creator_login']==developer_login):
            util.add(issues_comments_data, comment)
    if(len(issues_comments_data)>0):
        issues_comments_data.to_csv(path+'/issues_comments.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
    print('{}: Issues Comments Extraction Complete'.format(developer_login))
        
def get_pulls_comments_repo(gith, repo, project_name, start_date, active_users):
    path = super_path+'/'+project_name+'/Other_Activities'
    os.makedirs(path, exist_ok=True)
    
    exception_thrown = True
    while(exception_thrown):
        exception_thrown = False
        
        if 'pulls_comments_repo.csv' in os.listdir(path):
            pulls_comments_data = pandas.read_csv(path+'/pulls_comments_repo.csv', sep=',')
        else:
            pulls_comments_data = pandas.DataFrame(columns=['id','date','creator_login'])
        
        if 'pulls_comments_extraction.log' in os.listdir(path):
            last_pulls_page, last_pull, last_comments_page = get_last_page_read(path+'/pulls_comments_extraction.log')
        else:
            last_pulls_page=0
            last_pull='' 
            last_comments_page=0
            
        if 'comments_extraction_completed_pulls.csv' in os.listdir(path):
            completed_pulls = pandas.read_csv(path+'/comments_extraction_completed_pulls.csv', sep=',')
        else:
            completed_pulls = pandas.DataFrame(columns=['id'])

        logger = open(path+'/pulls_comments_extraction.log','a+')
        
        ### Get Comments on Pull
        try:
            pulls_page=0
            pull_id=''
            page=0
            
            pulls = repo.get_pulls(state='all', sort='created_at')
            num_pulls = pulls.totalCount
            final_pulls_page = int(num_pulls/cfg.items_per_page)            

            for pulls_page in range(last_pulls_page, final_pulls_page+1):
                cfg.waitRateLimit(gith)
                current_pulls_page = pulls.get_page(pulls_page)
                for pull in current_pulls_page:
                    cfg.waitRateLimit(gith)
                    pull_id=pull.id
                    if(pull_id not in completed_pulls.id.tolist()):
                        if(pull_id!=last_pull):
                            last_page=0
                        else:
                            last_page=last_comments_page
                        cfg.waitRateLimit(gith)
                        pulls_comments = pull.get_comments()
                        num_items = pulls_comments.totalCount
                        final_page = int(num_items/cfg.items_per_page)        
                        
                        for page in range(last_page, final_page+1):
                            cfg.waitRateLimit(gith)
                            pulls_comments_page = pulls_comments.get_page(page)
                            for comment in pulls_comments_page:
                                cfg.waitRateLimit(gith)
                                comment_id=comment.id
                                if(comment_id not in pulls_comments_data.id.tolist()):
                                    if(comment.user):
                                        cfg.waitRateLimit(gith)
                                        user_login=comment.user.login
                                        if(user_login in active_users):
                                            cfg.waitRateLimit(gith)
                                            util.add(pulls_comments_data, [comment_id, comment.created_at, user_login])
                        util.add(completed_pulls, pull_id)
            if(len(pulls_comments_data)>0):
                pulls_comments_data.to_csv(path+'/pulls_comments_repo.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
                completed_pulls.to_csv(path+'/comments_extraction_completed_pulls.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
                os.rename(path+'/pulls_comments_repo.csv', path+'/complete_pulls_comments_repo.csv')
            print('{}: Pulls Comments Extraction Complete'.format(repo))
        except github.GithubException:
            print('Exception Occurred While Getting PULLS COMMENTS: Github')
            logger.write('last_pulls_page:{},last_pull:{},last_comment_page:{}\n'.format(pulls_page, pull_id, page))
            logger.flush()
            if(len(pulls_comments_data)>0):
                pulls_comments_data.to_csv(path+'/pulls_comments_repo.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
                completed_pulls.to_csv(path+'/comments_extraction_completed_pulls.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
            exception_thrown=True
            pass
        except requests.exceptions.Timeout:
            print('Exception Occurred While Getting PULLS COMMENTS: Timeout')
            logger.write('last_pulls_page:{},last_pull:{},last_comment_page:{}\n'.format(pulls_page, pull_id, page))
            logger.flush()
            if(len(pulls_comments_data)>0):
                pulls_comments_data.to_csv(path+'/pulls_comments_repo.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
                completed_pulls.to_csv(path+'/comments_extraction_completed_pulls.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
            exception_thrown=True
            pass
        except:
            print('Execution Interrupted While Getting PULLS COMMENTS')
            logger.write('last_pulls_page:{},last_pull:{},last_comment_page:{}\n'.format(pulls_page, pull_id, page))
            logger.flush()
            if(len(pulls_comments_data)>0):
                pulls_comments_data.to_csv(path+'/pulls_comments_repo.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
                completed_pulls.to_csv(path+'/comments_extraction_completed_pulls.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
            raise
            
def get_pulls_comments_dev(project_name, developer_login):
    path = super_path+'/'+project_name+'/Other_Activities/'+developer_login
    os.makedirs(path, exist_ok=True) 
    
    ### Get Comments on Pull Requests 
    pulls_comments = pandas.read_csv(super_path+'/'+project_name+'/Other_Activities/complete_pulls_comments_repo.csv', sep=',')
    pulls_comments_data = pandas.DataFrame(columns=['id','date','creator_login'])

    for index, comment in pulls_comments.iterrows():
        if(comment['creator_login']==developer_login):
            util.add(pulls_comments_data, comment)
    if(len(pulls_comments_data)>0):
        pulls_comments_data.to_csv(path+'/pulls_comments.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
    print('{}: Pulls Comments Extraction Complete'.format(developer_login))
    
        
def get_issue_events_repo(gith, repo, project_name, start_date, active_users): #Why Not get_events()?
    path = super_path+'/'+project_name+'/Other_Activities'
    os.makedirs(path, exist_ok=True) 
    
    exception_thrown = True
    while(exception_thrown):
        exception_thrown = False
        
        if 'issues_events_repo.csv' in os.listdir(path):
            issues_events_data = pandas.read_csv(path+'/issues_events_repo.csv', sep=',')
        else:
            issues_events_data = pandas.DataFrame(columns=['id','date', 'event', 'creator_login'])
        
        if 'issues_events_extraction.log' in os.listdir(path):
            last_issues_page, last_issue, last_events_page = get_last_page_read(path+'/issues_events_extraction.log')
        else:
            last_issues_page=0
            last_issue='' 
            last_events_page=0
            
        if 'events_extraction_completed_issues.csv' in os.listdir(path):
            completed_issues = pandas.read_csv(path+'/events_extraction_completed_issues.csv', sep=',')
        else:
            completed_issues = pandas.DataFrame(columns=['id'])

        logger = open(path+'/issues_events_extraction.log','a+')
        
        ### Get Other Issues Events
        try:
            issues_page=0
            issue_id=''
            page=0
            
            issues = repo.get_issues(state='all', sort='created_at', since=start_date)
            num_issues = issues.totalCount
            final_issues_page = int(num_issues/cfg.items_per_page)         
        
            for issues_page in range(last_issues_page, final_issues_page+1):
                cfg.waitRateLimit(gith)
                current_issues_page = issues.get_page(issues_page)
                for issue in current_issues_page:
                    cfg.waitRateLimit(gith)
                    issue_id=issue.id
                    if(issue_id not in completed_issues.id.tolist()):
                        if(issue_id!=last_issue):
                            last_page=0
                        else:
                            last_page=last_events_page
                        cfg.waitRateLimit(gith)
                        issue_events = issue.get_events()
                        num_items = issue_events.totalCount
                        final_page = int(num_items/cfg.items_per_page)     
                        
                        for page in range(last_page, final_page+1):
                            cfg.waitRateLimit(gith)
                            issues_events_page = issue_events.get_page(page)
                            for event in issues_events_page:
                                cfg.waitRateLimit(gith)
                                event_id=event.id
                                if(event_id not in issues_events_data.id.tolist()):
                                    if(event.actor):
                                        cfg.waitRateLimit(gith)
                                        actor_login=event.actor.login
                                        if(actor_login in active_users):
                                            cfg.waitRateLimit(gith)
                                            util.add(issues_events_data, [event_id, event.created_at, event.event, actor_login])  
                        util.add(completed_issues, issue_id)     
            if(len(issues_events_data)>0):
                issues_events_data.to_csv(path+'/issues_events_repo.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
                completed_issues.to_csv(path+'/events_extraction_completed_issues.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
                os.rename(path+'/issues_events_repo.csv', path+'/complete_issues_events_repo.csv')
            print('{}: Issues Events Extraction Complete'.format(repo))
            
        except github.GithubException:
            print('Exception Occurred While Getting ISSUES EVENTS: Github')
            logger.write('last_issues_page:{},last_issue:{},last_event_page:{}\n'.format(issues_page, issue_id, page))
            logger.flush()
            if(len(issues_events_data)>0):
                issues_events_data.to_csv(path+'/issues_events_repo.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
                completed_issues.to_csv(path+'/events_extraction_completed_issues.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
            exception_thrown=True
            pass
        except requests.exceptions.Timeout:
            print('Exception Occurred While Getting ISSUES EVENTS: Timeout')
            logger.write('last_issues_page:{},last_issue:{},last_event_page:{}\n'.format(issues_page, issue_id, page))
            logger.flush()
            if(len(issues_events_data)>0):
                issues_events_data.to_csv(path+'/issues_events_repo.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
                completed_issues.to_csv(path+'/events_extraction_completed_issues.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
            exception_thrown=True
            pass
        except:
            print('Execution Interrupted While Getting ISSUES EVENTS')
            logger.write('last_issues_page:{},last_issue:{},last_event_page:{}\n'.format(issues_page, issue_id, page))
            logger.flush()
            if(len(issues_events_data)>0):
                issues_events_data.to_csv(path+'/issues_events_repo.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
                completed_issues.to_csv(path+'/events_extraction_completed_issues.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
            raise
            
def get_issue_events_dev(project_name, developer_login):
    path = super_path+'/'+project_name+'/Other_Activities/'+developer_login
    os.makedirs(path, exist_ok=True) 
    
    ### Get Other Issues Events
    issues_events = pandas.read_csv(super_path+'/'+project_name+'/Other_Activities/complete_issues_events_repo.csv', sep=',')
    issues_events_data = pandas.DataFrame(columns=['id','date', 'event', 'creator_login'])

    for index, event in issues_events.iterrows():
        if(event['creator_login']==developer_login):
            util.add(issues_events_data, event)
    if(len(issues_events_data)>0):
        issues_events_data.to_csv(path+'/issues_events.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
    print('{}: Issues Events Extraction Complete'.format(developer_login))
        
def get_activities(gith, repo, project_name, start_date, end_date, developer_login):
    get_issues_prs(gith, repo, project_name, start_date, developer_login)
    get_issues_comments_dev(project_name, developer_login)
    get_pulls_comments_dev(project_name, developer_login)
    get_issue_events_dev(project_name, developer_login)

    column_names=['action']
    for single_date in util.daterange(start_date, datetime.strptime(end_date, "%Y-%m-%d")):
        column_names.append(single_date.strftime("%Y-%m-%d"))
    
    ### Add Action Timeline to the Table
    path = super_path+'/'+project_name+'/Other_Activities/'+developer_login
    actions_data=[]
    if 'issues_pr_creation.csv' in os.listdir(path):
        issues_prs_data = pandas.read_csv(path+'/issues_pr_creation.csv', sep=',')
        actions_data.append(get_action_timeline("issues/pull_requests", issues_prs_data, column_names))
    if 'issues_comments.csv' in os.listdir(path):
        issues_comments_data = pandas.read_csv(path+'/issues_comments.csv', sep=',')
        actions_data.append(get_action_timeline("issues_comments", issues_comments_data, column_names))
    if 'pulls_comments.csv' in os.listdir(path):
        pulls_comments_data = pandas.read_csv(path+'/pulls_comments.csv', sep=',')
        actions_data.append(get_action_timeline("pull_requests_comments", pulls_comments_data, column_names))
    if 'issues_events.csv' in os.listdir(path):
        issues_events_data = pandas.read_csv(path+'/issues_events.csv', sep=',')
        actions_data.append(get_action_timeline("issues_events", issues_events_data, column_names))

    actions_table=pandas.DataFrame(actions_data,columns=column_names)
    #actions_table.to_csv(path+'all_actions_table.csv', sep=';', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
    return actions_table

def get_repo_activities(gith, repo, project_name, start_date, active_users):
    path=super_path+'/'+project_name+'/Other_Activities'
    os.makedirs(path, exist_ok=True) 
    files_in_path = os.listdir(path)
    
    if('complete_issues_comments_repo.csv' not in files_in_path):
        get_issues_comments_repo(gith, repo, project_name, start_date, active_users)
    if('complete_pulls_comments_repo.csv' not in files_in_path):
        get_pulls_comments_repo(gith, repo, project_name, start_date, active_users)
    if('complete_issues_events_repo.csv' not in files_in_path):
        get_issue_events_repo(gith, repo, project_name, start_date, active_users)
    