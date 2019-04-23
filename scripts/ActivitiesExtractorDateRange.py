# -*- coding: utf-8 -*-
"""
Created on Fri Feb  8 14:03:00 2019

@author: Pepp_
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Feb  6 11:09:58 2019

@author: Pepp_
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Dec 20 14:14:43 2018

@author: Pepp_
"""
### Import Library
import mysql.connector
import pandas
from datetime import timedelta#, date
from datetime import datetime
from matplotlib import pyplot
import numpy
import utilities as util
import config as cfg

config = cfg.config

### Open Connection
def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days+2)):
        yield start_date + timedelta(n)
        
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

def get_activities(project_name, partial_project_url, start_date, end_date, developer_id):
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor(buffered=True)
    
    PROJECT_ID = util.getProjectId(cursor, project_name, partial_project_url)

    actions_list=[]
    ### Get Pull Requests
    q_pull_requests = ("SELECT pull_request_id as id, created_at as date "+
                       "FROM pull_requests join pull_request_history "+
                       "on pull_requests.id=pull_request_history.pull_request_id "+
                       "WHERE head_repo_id="+PROJECT_ID+" AND actor_id="+developer_id+
                       " AND created_at>='"+start_date+"' AND created_at<='"+end_date+"'")
    cursor.execute(q_pull_requests)
    pull_requests_tab_fields = [i[0] for i in cursor.description]
    pull_requests_data=pandas.DataFrame(cursor.fetchall(), 
                                        columns=pull_requests_tab_fields)
    if(len(pull_requests_data)>0):
        actions_list.append('pull_request')
    else: 
        print("No Pull Requests")
     
    ### Get PR Comments
    q_pr_comments = ("SELECT comment_id as id, created_at as date "+
                     "FROM pull_requests join pull_request_comments "+
                     "on pull_requests.id=pull_request_comments.pull_request_id "+
                     "WHERE head_repo_id="+PROJECT_ID+" AND user_id="+developer_id+
                     " AND created_at>='"+start_date+"' AND created_at<='"+end_date+"'")
    cursor.execute(q_pr_comments)
    pr_comments_tab_fields = [i[0] for i in cursor.description]
    pr_comments_data=pandas.DataFrame(cursor.fetchall(),
                                      columns=pr_comments_tab_fields)
    if(len(pr_comments_data)>0):
        actions_list.append('pull_request_comments')
    else: 
        print("No Pull Request Comments")

    ### Get Issue Comments
    q_issue_comments = ("SELECT issues.issue_id as id, "+ 
             "issue_comments.created_at as date "+ 
             "FROM issues join issue_comments on issues.id=issue_comments.issue_id "+
             "WHERE repo_id="+PROJECT_ID+" AND user_id="+developer_id+
             " AND issue_comments.created_at>='"+start_date+"' AND issue_comments.created_at<='"+end_date+"'")
    cursor.execute(q_issue_comments)
    issue_comments_tab_fields = [i[0] for i in cursor.description]
    issue_comments_data=pandas.DataFrame(cursor.fetchall(), 
                                         columns=issue_comments_tab_fields)
    if(len(issue_comments_data)>0):
        actions_list.append('issue_comments')
    else:
        print("No Issue Comments")
    
    ### Get Issues Opened
    q_issues = ("SELECT id, created_at AS date "+
                "FROM issues WHERE repo_id="+PROJECT_ID+" AND reporter_id="+developer_id+
                " AND created_at>='"+start_date+"' AND created_at<='"+end_date+"'")
    cursor.execute(q_issues)
    issue_tab_fields = [i[0] for i in cursor.description]
    issues_data=pandas.DataFrame(cursor.fetchall(),
                                 columns=issue_tab_fields)
    if(len(issues_data)>0):    
        actions_list.append('issues_opened')
    else:
        print("No Issues Opened")
        
    # Other Issue Events
    q_issue_events = ("Select event_id AS id, issue_events.created_at AS date "+
                "FROM issues JOIN issue_events ON issues.id=issue_events.issue_id "+
                "WHERE repo_id="+PROJECT_ID+" AND actor_id="+developer_id+
                " AND issue_events.created_at>='"+start_date+"' AND issue_events.created_at<='"+end_date+"'")
    cursor.execute(q_issue_events)
    issue_events_tab_fields = [i[0] for i in cursor.description]
    issue_events_data=pandas.DataFrame(cursor.fetchall(),
                                              columns=issue_events_tab_fields)
    if(len(issue_events_data)>0):  
        actions_list.append('other_issue_events')
    else:
        print("No Issue Events")

    column_names=['action']
    for single_date in daterange(datetime.strptime(start_date, "%Y-%m-%d"), datetime.strptime(end_date, "%Y-%m-%d")):
        column_names.append(single_date.strftime("%Y-%m-%d"))
    
    ### Add Action Timeline to the Table
    actions_data=[]
    if('pull_request' in actions_list): 
        actions_data.append(get_action_timeline("pull_request", pull_requests_data, column_names))
    if('pull_request_comments' in actions_list): 
        actions_data.append(get_action_timeline("pull_request_comments", pr_comments_data, column_names))
    if('issue_comments' in actions_list): 
        actions_data.append(get_action_timeline("issue_comments", issue_comments_data, column_names))
    if('issues_opened' in actions_list): 
        actions_data.append(get_action_timeline("issues_opened", issues_data, column_names))
    if('other_issue_events' in actions_list): 
        actions_data.append(get_action_timeline("other_issue_events", issue_events_data, column_names))

    actions_table=pandas.DataFrame(actions_data,columns=column_names)
#    actions_table.to_csv(project_name+'/'+developer_id+'_'+username+'_actions_table.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
#    print("CSV Written")
    return actions_table

def plot_activities(activity_table, path_filename):
    actions = pandas.DataFrame()
    #actions.index=activity_table.index
    for action, a in activity_table.iterrows():
        actions[action] = pandas.Series(a)
    actions.plot(subplots=True, legend=True, use_index=True)#, sharex=True, use_index=True) 
    if len(actions)>=10:
        myStep=int(len(actions)/10)
    else:
        myStep=1
    pos=numpy.arange(len(actions),step=myStep)
    lables=actions.index.values.tolist()
    lables=numpy.reshape(lables,(len(lables),1))
    #labs=actions.index.values.tolist()
    valid_pos=pos.tolist()
    lables = lables[valid_pos,:]
    lables = numpy.reshape(lables,(len(lables)))
    pyplot.xticks(pos, lables) # location, labels
    #pyplot.xticks(numpy.arange(len(actions)), actions.index) # location, labels
    #pyplot.plot(len(actions))
    #pyplot.xticks(rotation=90)
    pyplot.savefig(path_filename, dpi=600)
    return
### TEST
#user_actions = get_activities('jabref', '/jabref/jabref', '2017-05-05', '2017-06-05', '65723')
## CHECK ACTIVITIES
#inner_start = '2017-05-08'
#inner_end = '2017-06-02'
#
#brake_actions = user_actions.loc[:,inner_start:inner_end] #Gets only the chosen period
#brake_actions.index=user_actions.action # Set the action name as a index
#brake_actions = brake_actions.loc[~(brake_actions==0).all(axis=1)] #Removes the actions not performed
#plot_activities(brake_actions, "C:/Users/Pepp_/SpyderWorkspace/Commit_Analysis/"+inner_start+"_"+inner_end) #PLOT CAREFUL!!!

def get_fork_activities(project_name, partial_project_url, start_date, end_date, developer_id):
    column_names=['action']
    for single_date in daterange(datetime.strptime(start_date, "%Y-%m-%d"), datetime.strptime(end_date, "%Y-%m-%d")):
        column_names.append(single_date.strftime("%Y-%m-%d"))
    actions_data=[]
    
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor(buffered=True)

    PROJECT_ID = util.getProjectId(cursor, project_name, partial_project_url)
    
    fork_id=''
    q_fork=("SELECT id from projects"+
            " WHERE owner_id="+developer_id+
            " AND forked_from="+PROJECT_ID)
    cursor.execute(q_fork)
    res = cursor.fetchone()
    if(res is not None):
        fork_id=str(res[0])
        print("Fork Found: "+fork_id)
    else:
        return fork_id, pandas.DataFrame(actions_data,columns=column_names)
        print("NO Fork Found")

    actions_list=[]
    ### Get Commits
    q_commits = ("SELECT id, created_at AS date FROM commits "+
                       "WHERE project_id="+PROJECT_ID+
                       " AND author_id="+developer_id+
                       " AND created_at>='"+start_date+"' AND created_at<='"+end_date+"'")
    cursor.execute(q_commits)
    commits_tab_fields = [i[0] for i in cursor.description]
    commit_data=pandas.DataFrame(cursor.fetchall(), 
                                        columns=commits_tab_fields)
    if(len(commit_data)>0):
        actions_list.append('commit')
    else: 
        print("No Fork Commits")
        
    ### Get Pull Requests
    q_pull_requests = ("SELECT pull_request_id as id, created_at as date "+
                       "FROM pull_requests join pull_request_history "+
                       "on pull_requests.id=pull_request_history.pull_request_id "+
                       "WHERE head_repo_id="+PROJECT_ID+" AND actor_id="+developer_id+
                       " AND created_at>='"+start_date+"' AND created_at<='"+end_date+"'")
    cursor.execute(q_pull_requests)
    pull_requests_tab_fields = [i[0] for i in cursor.description]
    pull_requests_data=pandas.DataFrame(cursor.fetchall(), 
                                        columns=pull_requests_tab_fields)
    if(len(pull_requests_data)>0):
        actions_list.append('pull_request')
    else: 
        print("No Fork Pull Requests")
     
    ### Get PR Comments
    q_pr_comments = ("SELECT comment_id as id, created_at as date "+
                     "FROM pull_requests join pull_request_comments "+
                     "on pull_requests.id=pull_request_comments.pull_request_id "+
                     "WHERE head_repo_id="+PROJECT_ID+" AND user_id="+developer_id+
                     " AND created_at>='"+start_date+"' AND created_at<='"+end_date+"'")
    cursor.execute(q_pr_comments)
    pr_comments_tab_fields = [i[0] for i in cursor.description]
    pr_comments_data=pandas.DataFrame(cursor.fetchall(),
                                      columns=pr_comments_tab_fields)
    if(len(pr_comments_data)>0):
        actions_list.append('pull_request_comments')
    else: 
        print("No Fork Pull Request Comments")

    ### Get Issue Comments
    q_issue_comments = ("SELECT issues.issue_id as id, "+ 
             "issue_comments.created_at as date "+ 
             "FROM issues join issue_comments on issues.id=issue_comments.issue_id "+
             "WHERE repo_id="+PROJECT_ID+" AND user_id="+developer_id+
             " AND issue_comments.created_at>='"+start_date+"' AND issue_comments.created_at<='"+end_date+"'")
    cursor.execute(q_issue_comments)
    issue_comments_tab_fields = [i[0] for i in cursor.description]
    issue_comments_data=pandas.DataFrame(cursor.fetchall(), 
                                         columns=issue_comments_tab_fields)
    if(len(issue_comments_data)>0):
        actions_list.append('issue_comments')
    else:
        print("No Fork Issue Comments")
    
    ### Get Issues Opened
    q_issues = ("SELECT id, created_at AS date "+
                "FROM issues WHERE repo_id="+PROJECT_ID+" AND reporter_id="+developer_id+
                " AND created_at>='"+start_date+"' AND created_at<='"+end_date+"'")
    cursor.execute(q_issues)
    issue_tab_fields = [i[0] for i in cursor.description]
    issues_data=pandas.DataFrame(cursor.fetchall(),
                                 columns=issue_tab_fields)
    if(len(issues_data)>0):    
        actions_list.append('issues_opened')
    else:
        print("No Fork Issues Opened")
        
    # Other Issue Events
    q_issue_events = ("Select event_id AS id, issue_events.created_at AS date "+
                "FROM issues JOIN issue_events ON issues.id=issue_events.issue_id "+
                "WHERE repo_id="+PROJECT_ID+" AND actor_id="+developer_id+
                " AND issue_events.created_at>='"+start_date+"' AND issue_events.created_at<='"+end_date+"'")
    cursor.execute(q_issue_events)
    issue_events_tab_fields = [i[0] for i in cursor.description]
    issue_events_data=pandas.DataFrame(cursor.fetchall(),
                                              columns=issue_events_tab_fields)
    if(len(issue_events_data)>0):  
        actions_list.append('other_issue_events')
    else:
        print("No Fork Issue Events")

    ### Add Action Timeline to the Table
    if('commit' in actions_list): 
        actions_data.append(get_action_timeline("fork_commit", commit_data, column_names))
    if('pull_request' in actions_list): 
        actions_data.append(get_action_timeline("fork_pull_request", pull_requests_data, column_names))
    if('pull_request_comments' in actions_list): 
        actions_data.append(get_action_timeline("fork_pull_request_comments", pr_comments_data, column_names))
    if('issue_comments' in actions_list): 
        actions_data.append(get_action_timeline("fork_issue_comments", issue_comments_data, column_names))
    if('issues_opened' in actions_list): 
        actions_data.append(get_action_timeline("fork_issues_opened", issues_data, column_names))
    if('other_issue_events' in actions_list): 
        actions_data.append(get_action_timeline("fork_other_issue_events", issue_events_data, column_names))

    actions_table=pandas.DataFrame(actions_data,columns=column_names)
#    actions_table.to_csv(project_name+'/'+developer_id+'_'+username+'_actions_table.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
#    print("CSV Written")
    return fork_id, actions_table