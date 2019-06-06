import mysql.connector
import utilities as util
import pandas, csv, os
from datetime import datetime, timedelta
import ActivitiesExtractorDateRange as aedr
import logging
import config as cfg

config = cfg.config

p_names=cfg.p_names
p_urls=cfg.p_urls
super_path = cfg.super_path

START_FROM = 0
projects_stats=pandas.DataFrame(columns=['Project','Contributors','Sampled_Contributors','Sleeping','Hibernated','Dead'])

for i in range(START_FROM, len(p_names)):
    chosen_project = i # FROM 0 TO n-1
    
    project_name =  p_names[chosen_project]
    partial_project_url = p_urls[chosen_project]
    
    cnx = mysql.connector.connect(**config)
    cursor = cnx.cursor(buffered=True)
    
    project_id = util.getProjectId(cursor, project_name, partial_project_url)
    
    #Read Commit Table
    commit_table = pandas.read_csv(super_path+'/'+project_name+'/commit_table.csv') 
    project_start=min(commit_table.columns[1:])
    project_end='2019-01-01' #max(commit_table.columns[1:])

    #Read Breaks Table
    with open(super_path+'/'+project_name+'/inactivity_interval_list.csv', 'r') as f:  #opens PW file
        reader = csv.reader(f)
        inactivity_intervals_data = [list(map(float,rec)) for rec in csv.reader(f, delimiter=',')]
    
    #Read Break Dates Table
    with open(super_path+'/'+project_name+'/break_dates_list.csv', 'r') as f:
        reader = csv.reader(f)
        break_dates_data = [list(map(str,rec)) for rec in csv.reader(f, delimiter=',')]
    
    breaks_df = pandas.DataFrame({'durations' : inactivity_intervals_data, 'datelimits' : break_dates_data})
    
    # FILTER DEVELOPERS
    SLIDE_WIN_SIZE = 20

    active_users_df = pandas.DataFrame(columns=['durations','datelimits'])
    
    path = (super_path+'/'+project_name)
    util.reportPlotProjectBreaksDistribution(breaks_df['durations'], project_name, path)
    
    for index, row in breaks_df.iterrows():
        #Constraint on #Commit_Days: (row['durations'][0] in core_user_ids)
        #Constraint on Lifespan: (row['durations'][-6]>lifespan_th)
        #Constraint on #Breaks: (num_breaks>=breaks_number_th)
        num_breaks=len(row['durations'])-7
        if ((num_breaks>=SLIDE_WIN_SIZE)):
            util.add(active_users_df, row)
    num_all_users = len(inactivity_intervals_data)
    num_active_users = len(active_users_df)
    
    logging.basicConfig(filename=super_path+'/Analyzer.log',level=logging.INFO)
    logging.info('Project: '+project_name+' PID: '+project_id+' Start: '+project_start+ ' End: '+project_end)
    logging.info('All Users: '+str(num_all_users)+' Breaks_Threshold/Sliding_Window: '+str(SLIDE_WIN_SIZE)+' Active Users: '+str(num_active_users))

    path = (super_path+'/'+project_name+"/Activities_Plots")
    os.makedirs(path, exist_ok=True) 
    
    active_users_longer_intervals=[]
    
    active_devs_sleeping_intervals_df = []
    active_devs_hibernation_intervals_df = []
    active_devs_dead_intervals_df = []
    
    n=0
    for index, row in active_users_df.iterrows():
        user_id=int(row['durations'][0])
        
        last_commit_day=util.getLastCommitDay(commit_table, user_id)
        last_break_length=util.days_between(last_commit_day, project_end)
        last_break_interval=last_commit_day+'/'+project_end
        
        row['durations'] = row['durations'][1:-6]
        row['durations'].append(last_break_length)
        row['datelimits'] = row['datelimits'][1:]
        row['datelimits'].append(last_break_interval)
        
        path = (super_path+'/'+project_name+'/Activities_Plots/'+str(user_id))
        os.makedirs(path, exist_ok=True) 
        
        if 'actions_table.csv' in os.listdir(path):
            user_actions = pandas.read_csv(path+'/actions_table.csv', sep=';')
        else:
            user_actions = aedr.get_activities(project_name, partial_project_url, project_start, project_end, str(user_id))
            if not user_actions.empty: user_actions.to_csv(path+"/actions_table.csv", sep=';', encoding='utf-8', na_rep='NA', header=True, index=False, mode='w', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
        
        #Check if the developer owns a fork
        #fork_id, user_fork_actions = aedr.get_fork_activities(project_name, partial_project_url, project_start, project_end, str(user_id))
        #if not user_fork_actions.empty: user_fork_actions.to_csv(path+"/fork_actions_table.csv", sep=';', encoding='utf-8')
                    
        longer_breaks = pandas.DataFrame(columns=['durations', 'datelimits'])
        current_user_hibernation_periods_df = pandas.DataFrame(columns=['durations', 'datelimits'])
        current_user_sleepy_periods_df = pandas.DataFrame(columns=['durations', 'datelimits'])
        current_user_dead_periods_df=pandas.DataFrame(columns=['durations', 'datelimits'])
        dead_th = cfg.dead_threshold

        current_sleepy_periods_details=[]
        
        for i in range(0, len(row['durations'])-SLIDE_WIN_SIZE):
            w_start = i 
            w_end = i + SLIDE_WIN_SIZE
            
            # COMPUTE WONDOW THRESHOLD (Far Out Values)
            threshold = util.getFarOutThreshold(row['durations'][w_start:w_end])
        
            for j in range(w_start,w_end+1):
                duration = row['durations'][j]
                date_range = row['datelimits'][j]
                if((duration>threshold) & (date_range not in longer_breaks.datelimits.tolist())):
                    util.add(longer_breaks, [duration, date_range])
                    
                    # CHECK ACTIVITIES
                    break_range = date_range.split('/')
                    inner_start = (datetime.strptime(break_range[0], "%Y-%m-%d")+timedelta(days=1)).strftime("%Y-%m-%d")
                    inner_end = (datetime.strptime(break_range[1], "%Y-%m-%d")-timedelta(days=1)).strftime("%Y-%m-%d")
                    
                    brake_actions = user_actions.loc[:,inner_start:inner_end] #Gets only the chosen period
                    brake_actions.index=user_actions.action # Set the action name as a index
                    brake_actions = brake_actions.loc[~(brake_actions==0).all(axis=1)] #Removes the actions not performed
                    
                    """
                    
                    brake_fork_actions = user_fork_actions.loc[:,inner_start:inner_end] #Gets only the chosen period
                    brake_fork_actions.index=user_fork_actions.action # Set the action name as a index
                    brake_fork_actions = brake_fork_actions.loc[~(brake_fork_actions==0).all(axis=1)] #Removes the actions not performed
                    
                    all_brake_actions = pandas.concat([brake_actions, brake_fork_actions])
                    
                    When Uncomment please CHANGE in the next instruction brake_actions WITH all_brake_actions and UNCOMMENT FORK TABLE EXTRACTION
                    """
                    is_activity_day = (brake_actions != 0).any() #List Of Columns With at least a Non-Zero Value
                    action_days = is_activity_day.index[is_activity_day].tolist() #List Of Columns NAMES Having Column Names at least a Non-Zero Value
                    # entire_active_columns = all_brake_actions.columns[is_activity_day]
                    
                    if(len(brake_actions)>0):
                        #aedr.plot_activities(brake_actions, path+"/"+break_range[0]+"_"+break_range[1]) #PLOT CAREFUL!!!
                        
                        sleepy_period_detail=util.refineSleepingPeriod(duration, date_range, action_days, threshold)
                        current_sleepy_periods_details.append(sleepy_period_detail)
                        
                        current_sleepings_only=util.getSleepingsFromSleepingDetail(sleepy_period_detail)
                        current_user_sleepy_periods_df=pandas.concat([current_user_sleepy_periods_df, current_sleepings_only])

                        other_current_hibernations_df = util.getHibernationsFromSleepingDetail(sleepy_period_detail)
                        current_user_hibernation_periods_df = pandas.concat([current_user_hibernation_periods_df, other_current_hibernations_df])
                        
                        other_current_deads_df = util.getDeadsFromSleepingDetail(sleepy_period_detail)
                        current_user_dead_periods_df = pandas.concat([current_user_dead_periods_df, other_current_deads_df])
                    else:##ELIF HAS ACTIVITIES IN THE FORK
                        #The whole period goes in the HYBERNATED ones
                        if(duration>dead_th):
                            util.add(current_user_dead_periods_df, [duration,date_range])
                        else:
                            util.add(current_user_hibernation_periods_df, [duration,date_range])                  
        
        active_users_longer_intervals.append(longer_breaks)
        
        path = (super_path+'/'+project_name+"/Sleeping&Awaken_Users/Details")
        os.makedirs(path, exist_ok=True) 
        
        if(len(current_sleepy_periods_details)>0):
            with open(path+'/'+str(user_id)+'.csv', 'w', newline='') as outcsv:   
                writer = csv.writer(outcsv, quoting=csv.QUOTE_ALL, quotechar='"')
                for row in current_sleepy_periods_details:
                    writer.writerow(row)
              
        current_user_sleepings = [user_id]
        current_user_hibernations = [user_id]
        current_user_deads = [user_id]

        if(len(current_user_sleepy_periods_df)>0):
            current_user_sleepings.append(current_user_sleepy_periods_df)
            active_devs_sleeping_intervals_df.append(current_user_sleepings)
        if(len(current_user_hibernation_periods_df)>0):
            current_user_hibernations.append(current_user_hibernation_periods_df)
            active_devs_hibernation_intervals_df.append(current_user_hibernations)
        if(len(current_user_dead_periods_df)>0):
            current_user_deads.append(current_user_dead_periods_df)
            active_devs_dead_intervals_df.append(current_user_deads)
        
        n += 1
        print('Complete '+str(user_id)+': Developer '+str(n)+' of '+str(num_active_users)+' Index is '+str(index))
    
    num_sleeping_users = len(active_devs_sleeping_intervals_df)
    path = (super_path+'/'+project_name+"/Sleeping&Awaken_Users")
    util.writeUsersCSV_byItem(cursor, active_devs_sleeping_intervals_df, path)
    
    num_hibernation_users = len(active_devs_hibernation_intervals_df)
    path = (super_path+'/'+project_name+"/Hibernated&Unfrozen_Users")
    util.writeUsersCSV_byItem(cursor, active_devs_hibernation_intervals_df, path)
    
    num_dead_users = len(active_devs_dead_intervals_df)
    path = (super_path+'/'+project_name+"/Dead&Resurrected_Users")
    util.writeUsersCSV_byItem(cursor, active_devs_dead_intervals_df, path)
    
    full_sleepings_list = util.getSleepingsList(super_path, project_name)
    full_hibernated_list = util.getHibernationsList(super_path, project_name) # Includes Deads because they have been Hibernated before
    full_dead_list = util.getDeadsList(super_path, project_name)
    util.add(projects_stats, [project_name, num_all_users, num_active_users, len(full_sleepings_list), len(full_hibernated_list), len(full_dead_list)])
    project_transitions=util.countDevTransitions(super_path, project_name, breaks_df['durations'], cursor)
    durations = util.reportDevsBreaksLengthDistribution(project_name, super_path, cursor)
    durations.to_csv(super_path+'/dev_statuses_durations.csv', sep=';', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
    cnx.close()
    
# Write Final Table
projects_stats.to_csv(super_path+'/projects_stats.csv', sep=';', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
util.tableCumulativeTransitions(cfg.p_names, cfg.super_path)
util.tableCumulativeTransitionsPercentages(super_path)
util.tableTransitionsPercentagesProjectList(cfg.p_names, cfg.super_path)
util.reportPlotAllProjectBreaksDistribution(cfg.p_names, cfg.super_path)
util.tableTransitionsPercentages(cfg.p_names, cfg.super_path)
util.printProjectsDurationsLog(cfg.p_names, cfg.super_path)
util.printProjectsDurations(cfg.p_names, cfg.super_path)
util.plotAllProjectInactivities(cfg.p_names)
